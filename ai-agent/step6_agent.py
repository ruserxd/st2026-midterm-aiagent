"""步驟 6：最終版 agent。處理前面幾步觀察到的失敗模式，並把所有實驗條件整合成參數。

前面觀察到的問題，以及這一步的處理方式（兩種模式套用完全相同的規則）：

  問題                                    處理
  ------------------------------------    ---------------------------------------------------
  步數上限 15，ReAct + 範例剛好用完          上限提高到 25
  任務說「at most 15 steps」，模型可能       預設不告訴模型步數上限（--tell-limit 可以打開）
    為了省步數而少讀規格（假設 F10）
  模型只講話、不呼叫工具                     提醒它；連續 3 次就結束這一輪
  和上一步完全相同的呼叫（重複迴圈）          照常執行，但在結果後加註提醒；連續 3 次就結束
  重寫測試卻只改了註解（F8）                 不干預，只記錄次數（noop_rewrites）
  模型輸出格式錯誤的工具呼叫（HTTP 500）       同一請求重試最多 3 次；仍失敗就告訴模型格式錯誤，
    （步驟 8 第一批：9/25 次因此中斷）          讓它重新呼叫；連續 3 步都失敗才結束

每次執行都記錄 stop_reason：finish / step_limit / no_tool_calls / loop / llm_error

執行：
    python3 step6_agent.py react
    python3 step6_agent.py act
    python3 step6_agent.py react --fewshot
    python3 step6_agent.py act --fewshot
    python3 step6_agent.py react --fewshot --tell-limit
結果存在 runs/exp/<條件>/run_<時間>/（條件名稱例如 react+fewshot+limit）
"""

import argparse
import ast
import json
import shutil
import time
from datetime import datetime

import requests

from step1_call_llm import MODEL, OLLAMA_URL
from step3_act_agent import KEEP_THINKING, NUM_CTX, ROOT, TEST_FILE, WORKSPACE, execute
from step4_react_agent import schemas_for, short, system_prompt_for
from step5_fewshot_agent import EXEMPLAR_ACT, EXEMPLAR_REACT, INTRO

MAX_STEPS = 25
MAX_NO_TOOL = 3          # 連續幾次不呼叫工具就結束
MAX_REPEATS = 3          # 連續幾次重複同一個呼叫就結束
MAX_LLM_ATTEMPTS = 3     # 呼叫模型失敗時，同一個請求最多試幾次
MAX_PARSE_FAILS = 3      # 連續幾步「重試後仍無法解析」就結束
PARSE_ERROR_NOTE = ("Your previous tool call could not be parsed: the arguments were not valid JSON. "
                    "Call the tool again with valid JSON arguments and nothing else.")
EXP_DIR = ROOT / "runs" / "exp"

REPEAT_NOTE = ("\n\n[Note: this call is identical to your previous one, so the result is the same. "
               "Do something different.]")


def call_llm(messages, schemas, think="low", num_ctx=NUM_CTX):
    """和步驟 4 的 call_llm 相同，只是推理強度（think）與上下文長度（num_ctx）改成參數。"""
    payload = {"model": MODEL, "messages": messages, "tools": schemas, "stream": False,
               "think": think, "options": {"num_ctx": num_ctx}}
    resp = requests.post(OLLAMA_URL, json=payload, timeout=900)
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    msg = data["message"]
    return {"content": msg.get("content", ""), "thinking": msg.get("thinking", ""),
            "tool_calls": msg.get("tool_calls") or [],
            "input_tokens": data.get("prompt_eval_count", 0),
            "output_tokens": data.get("eval_count", 0),
            "done_reason": data.get("done_reason", "")}


def build_system_prompt(mode, fewshot):
    prompt = system_prompt_for(mode)                     # 步驟 4：規則（ReAct 多一句）
    if fewshot:                                          # 步驟 5：加上範例
        prompt += INTRO[mode] + (EXEMPLAR_REACT if mode == "react" else EXEMPLAR_ACT)
    return prompt


def build_task(max_steps, tell_limit):
    task = "Module under test: `cart`. Write test_cart.py."
    if tell_limit:
        task += f" You have at most {max_steps} steps."
    return task


def same_tests(old_code, new_code):
    """兩版測試的程式結構是否相同。ast 會忽略註解與空白，所以「只改註解」會判定為相同。"""
    try:
        return ast.dump(ast.parse(old_code)) == ast.dump(ast.parse(new_code))
    except SyntaxError:
        return False


def run_agent(mode, fewshot=False, max_steps=MAX_STEPS, tell_limit=False, verbose=True,
              keep_thinking=KEEP_THINKING, think="low", num_ctx=NUM_CTX,
              out_dir=None):
    condition = (mode + ("+fewshot" if fewshot else "") + ("+limit" if tell_limit else "")
                 + ("+keep" if keep_thinking else "") + (f"+{think}" if think != "low" else ""))
    base_dir = out_dir or EXP_DIR
    run_dir = base_dir / condition / f"run_{datetime.now():%Y%m%d-%H%M%S}"
    k = 1
    while run_dir.exists():                              # 同一秒內連續執行時避免撞名
        k += 1
        run_dir = run_dir.with_name(f"run_{datetime.now():%Y%m%d-%H%M%S}_{k}")
    run_dir.mkdir(parents=True)
    WORKSPACE.mkdir(exist_ok=True)
    if TEST_FILE.exists():
        TEST_FILE.unlink()

    system = build_system_prompt(mode, fewshot)
    task = build_task(max_steps, tell_limit)
    (run_dir / "system_prompt.txt").write_text(system + "\n\n=== TASK ===\n" + task, encoding="utf-8")

    schemas = schemas_for(mode)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    stats = {"condition": condition, "mode": mode, "fewshot": fewshot, "model": MODEL,
             "max_steps": max_steps, "tell_limit": tell_limit, "keep_thinking": keep_thinking, "think": think, "num_ctx": num_ctx,
             "steps": 0, "stop_reason": "step_limit", "tool_calls": {},
             "no_tool_call": 0, "repeated_calls": 0, "noop_rewrites": 0, "missing_thought": 0,
             "llm_retries": 0, "parse_failures": 0, "context_full_steps": 0,
             "input_tokens": 0, "output_tokens": 0, "thinking_chars": 0, "thought_chars": 0,
             "finish_summary": None}
    log = []
    prev_call, repeat_streak, no_tool_streak, last_code = None, 0, 0, None
    parse_fail_streak = 0
    t_start = time.time()

    def say(*parts):
        if verbose:
            print(*parts)

    for n in range(1, max_steps + 1):
        t0 = time.time()
        stats["steps"] = n

        # ---- 呼叫模型；失敗就重試（模型輸出有隨機性，重送通常會成功）----
        reply, errors = None, []
        for attempt in range(MAX_LLM_ATTEMPTS):
            try:
                reply = call_llm(messages, schemas, think, num_ctx)
                break
            except Exception as exc:
                errors.append(str(exc))
                stats["llm_retries"] += 1
                say(f"[Step {n}] 第 {attempt + 1} 次呼叫失敗：{str(exc)[:120]}")
                time.sleep(2)

        if reply is None:
            log.append({"step": n, "llm_error": errors})
            if all("error parsing tool call" in e for e in errors):
                # 格式錯誤：告訴模型，讓它重新呼叫（這一步不會留下模型的輸出）
                stats["parse_failures"] += 1
                parse_fail_streak += 1
                messages.append({"role": "user", "content": PARSE_ERROR_NOTE})
                if parse_fail_streak >= MAX_PARSE_FAILS:
                    stats["stop_reason"] = "llm_error"
                    say(f"[停止] 連續 {MAX_PARSE_FAILS} 步都無法解析工具呼叫")
                    break
                continue
            stats["stop_reason"] = "llm_error"                   # 其他錯誤（連線、逾時）：停止
            say(f"[停止] 呼叫模型失敗：{errors[-1][:200]}")
            break
        parse_fail_streak = 0
        stats["input_tokens"] += reply["input_tokens"]
        stats["output_tokens"] += reply["output_tokens"]
        # 輸入 + 輸出 用滿了上下文：這一步的輸出（多半是內部思考）被硬生生截斷
        if (reply["input_tokens"] + reply["output_tokens"] >= num_ctx
                or reply["done_reason"] == "length"):
            stats["context_full_steps"] += 1
        stats["thinking_chars"] += len(reply["thinking"])
        say(f"\n===== [{condition}] Step {n}  ({time.time() - t0:.1f}s, "
            f"in={reply['input_tokens']} out={reply['output_tokens']}) =====")

        msg = {"role": "assistant", "content": reply["content"], "tool_calls": reply["tool_calls"]}
        if keep_thinking:                 # 把內部思考放回歷史。Ollama 的 gpt-oss 樣板只會把
            msg["thinking"] = reply["thinking"]   # 「最後一則 user 訊息之後」的 thinking 放進 prompt
        messages.append(msg)

        # ---- 沒有呼叫工具 ----
        if not reply["tool_calls"]:
            stats["no_tool_call"] += 1
            no_tool_streak += 1
            observation = "You did not call a tool. Call exactly one of the tools."
            messages.append({"role": "user", "content": observation})
            say("[文字輸出]", reply["content"].strip()[:150])
            log.append({"step": n, **reply, "observation": observation})
            if no_tool_streak >= MAX_NO_TOOL:
                stats["stop_reason"] = "no_tool_calls"
                say(f"[停止] 連續 {MAX_NO_TOOL} 次沒有呼叫工具")
                break
            continue
        no_tool_streak = 0

        # ---- 執行每個工具呼叫 ----
        for call in reply["tool_calls"]:
            name = call["function"]["name"]
            args = dict(call["function"].get("arguments") or {})
            thought = args.pop("thought", None)
            if mode == "react":
                if thought:
                    stats["thought_chars"] += len(thought)
                else:
                    stats["missing_thought"] += 1
                say("[Thought]", thought or "（沒有寫）")

            key = (name, json.dumps(args, sort_keys=True))
            repeated = key == prev_call
            repeat_streak = repeat_streak + 1 if repeated else 0
            stats["repeated_calls"] += repeated
            prev_call = key
            stats["tool_calls"][name] = stats["tool_calls"].get(name, 0) + 1

            if name == "write_tests" and isinstance(args.get("code"), str):
                if last_code is not None and same_tests(last_code, args["code"]):
                    stats["noop_rewrites"] += 1
                last_code = args["code"]

            observation = execute(name, args)
            if repeated and name != "finish":
                observation += REPEAT_NOTE
            messages.append({"role": "tool", "tool_name": name, "content": observation})
            say(f"[Action] {name}({json.dumps({k: short(v) for k, v in args.items()}, ensure_ascii=False)})")
            say("[Observation]", observation[:400])
            log.append({"step": n, **reply, "thought": thought, "action": name, "args": args,
                        "repeated": repeated, "observation": observation})

            if name == "finish":
                stats["stop_reason"] = "finish"
                stats["finish_summary"] = args.get("summary")
                break
        if stats["stop_reason"] == "finish":
            break
        if repeat_streak >= MAX_REPEATS:
            stats["stop_reason"] = "loop"
            say(f"[停止] 連續 {MAX_REPEATS} 次重複同一個呼叫")
            break

    stats["wall_seconds"] = round(time.time() - t_start, 1)
    (run_dir / "trajectory.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    if TEST_FILE.exists():
        shutil.copy(TEST_FILE, run_dir / "test_cart.py")

    say("\n========== 統計 ==========")
    for k, v in stats.items():
        if k != "finish_summary":
            say(f"{k:16s} {v}")
    say(f"\n結果存在 {run_dir}")
    return run_dir, stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["react", "act"])
    ap.add_argument("--fewshot", action="store_true", help="加上步驟 5 的範例")
    ap.add_argument("--max-steps", type=int, default=MAX_STEPS)
    ap.add_argument("--tell-limit", action="store_true", help="在任務中告訴模型步數上限")
    ap.add_argument("--keep-thinking", action="store_true", help="把模型的內部思考放回歷史")
    ap.add_argument("--think", default="low", choices=["low", "medium", "high"], help="gpt-oss 的推理強度")
    ap.add_argument("--num-ctx", type=int, default=NUM_CTX, help="上下文長度（token）")
    a = ap.parse_args()
    run_agent(a.mode, a.fewshot, a.max_steps, a.tell_limit, keep_thinking=a.keep_thinking, think=a.think,
              num_ctx=a.num_ctx)