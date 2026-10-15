"""步驟 4：加入 Thought，變成 ReAct agent。同一支程式也能跑 Act，方便對照。

ReAct 的核心（論文第 2 節）：把動作空間擴充成 Â = A ∪ L。
Thought 是一種「不影響環境」的動作，它的作用是寫進上下文，幫助之後的推理與行動。

我們的做法：ReAct 模式下，每個工具都多一個必填參數 `thought`。
  - 模型每次呼叫工具，都必須先寫下理由
  - 這段理由會跟著工具呼叫一起留在 messages 裡，之後每一步都看得到
  - 執行工具時把 thought 拿掉，所以它不會改變環境（和論文的定義一致）
Act 模式則完全沿用步驟 3：工具沒有 thought 參數。
兩種模式只差這一個參數和 system prompt 裡的一句話，其他全部相同（控制變因）。

執行：
    python3 step4_react_agent.py react
    python3 step4_react_agent.py act
每次執行的結果存在 runs/<模式>_<時間>/，不會互相覆蓋。
"""

import copy
import json
import shutil
import sys
import time
from datetime import datetime

import requests

from step1_call_llm import MODEL, OLLAMA_URL
from step3_act_agent import (KEEP_THINKING, MAX_STEPS, NUM_CTX, ROOT, TASK, TEST_FILE,
                             TOOL_SCHEMAS, TOOLS, WORKSPACE, execute)

RUNS_DIR = ROOT / "runs"

# =====================================================================
# 1. 兩種模式的工具說明書
# =====================================================================
THOUGHT_DESC = ("Your reasoning before this action: reason about the current situation "
                "and why this action is the right next step.")


def schemas_for(mode):
    """Act：原本的工具。ReAct：每個工具的第一個參數多一個必填的 thought。"""
    if mode == "act":
        return TOOL_SCHEMAS
    schemas = copy.deepcopy(TOOL_SCHEMAS)            # 複製一份，不改到原本的
    for s in schemas:
        params = s["function"]["parameters"]
        params["properties"] = {"thought": {"type": "string", "description": THOUGHT_DESC},
                                **params["properties"]}
        params["required"] = ["thought"] + params["required"]
    return schemas


# =====================================================================
# 2. 兩種模式的 system prompt：規則相同，ReAct 只多一句
# =====================================================================
BASE_PROMPT = """You are a software testing agent. Use the tools to write a pytest test suite for the Python module `cart` and to check whether the module follows its SPECIFICATION (its docstrings).

Rules:
- The test file must use `import cart`.
- Expected values must come from the specification. The implementation may contain bugs.
- When you are done, call finish with a summary of every place where the module disagrees with its specification."""

# 這句話取自論文 HotpotQA prompt 的說法："Thought can reason about the current situation"
REACT_EXTRA = """
- Every tool has a `thought` argument. Before each action, use it to reason about the current situation."""


def system_prompt_for(mode):
    return BASE_PROMPT + (REACT_EXTRA if mode == "react" else "")


# =====================================================================
# 3. 呼叫 LLM：工具說明書改成由參數傳入
# =====================================================================
def call_llm(messages, schemas):
    payload = {"model": MODEL, "messages": messages, "tools": schemas, "stream": False,
               "think": "low", "options": {"num_ctx": NUM_CTX}}
    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    msg = data["message"]
    return {"content": msg.get("content", ""), "thinking": msg.get("thinking", ""),
            "tool_calls": msg.get("tool_calls") or [],
            "input_tokens": data.get("prompt_eval_count", 0),
            "output_tokens": data.get("eval_count", 0)}


def short(value, n=80):
    return value[:n] + "..." if isinstance(value, str) and len(value) > n else value


# =====================================================================
# 4. Agent 迴圈（和步驟 3 幾乎一樣，多了 thought 的處理與統計）
# =====================================================================
def run_agent(mode):
    assert mode in ("react", "act"), "模式只能是 react 或 act"
    run_dir = RUNS_DIR / f"{mode}_{datetime.now():%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True)
    WORKSPACE.mkdir(exist_ok=True)
    if TEST_FILE.exists():
        TEST_FILE.unlink()

    schemas = schemas_for(mode)
    messages = [{"role": "system", "content": system_prompt_for(mode)},
                {"role": "user", "content": TASK}]
    stats = {"mode": mode, "model": MODEL, "steps": 0, "finished": False,
             "tool_calls": {}, "no_tool_call": 0, "repeated_calls": 0,
             "missing_thought": 0, "input_tokens": 0, "output_tokens": 0,
             "thinking_chars": 0, "thought_chars": 0, "finish_summary": None}
    log, prev_call = [], None
    t_start = time.time()

    for n in range(1, MAX_STEPS + 1):
        t0 = time.time()
        try:
            reply = call_llm(messages, schemas)
        except Exception as exc:
            print(f"\n[Step {n}] 呼叫模型失敗，停止：{exc}")
            log.append({"step": n, "llm_error": str(exc)})
            break
        stats["steps"] = n
        stats["input_tokens"] += reply["input_tokens"]
        stats["output_tokens"] += reply["output_tokens"]
        stats["thinking_chars"] += len(reply["thinking"])

        print(f"\n===== [{mode}] Step {n}  ({time.time() - t0:.1f}s, "
              f"in={reply['input_tokens']} out={reply['output_tokens']}) =====")
        print("[內部思考]", reply["thinking"][:150].replace("\n", " "))

        assistant_msg = {"role": "assistant", "content": reply["content"],
                         "tool_calls": reply["tool_calls"]}       # thought 就在 tool_calls 的參數裡
        if KEEP_THINKING:
            assistant_msg["thinking"] = reply["thinking"]
        messages.append(assistant_msg)

        if not reply["tool_calls"]:
            stats["no_tool_call"] += 1
            observation = "You did not call a tool. Call exactly one of the tools."
            messages.append({"role": "user", "content": observation})
            print("[文字輸出]", reply["content"].strip()[:200])
            print("[Observation]", observation)
            log.append({"step": n, **reply, "observation": observation})
            continue

        for call in reply["tool_calls"]:
            name = call["function"]["name"]
            args = dict(call["function"].get("arguments") or {})
            thought = args.pop("thought", None)          # Thought 不傳給工具：它不影響環境

            if mode == "react":
                if thought:
                    stats["thought_chars"] += len(thought)
                    print("[Thought]", thought)
                else:
                    stats["missing_thought"] += 1
                    print("[Thought] （沒有寫）")

            key = (name, json.dumps(args, sort_keys=True))
            if key == prev_call:
                stats["repeated_calls"] += 1             # 和上一步完全相同的呼叫
            prev_call = key
            stats["tool_calls"][name] = stats["tool_calls"].get(name, 0) + 1

            observation = execute(name, args)
            messages.append({"role": "tool", "tool_name": name, "content": observation})
            print(f"[Action] {name}({json.dumps({k: short(v) for k, v in args.items()}, ensure_ascii=False)})")
            print("[Observation]", observation[:600])
            log.append({"step": n, **reply, "thought": thought, "action": name,
                        "args": args, "observation": observation})

            if name == "finish":
                stats["finished"] = True
                stats["finish_summary"] = args.get("summary")
                break
        if stats["finished"]:
            break

    stats["wall_seconds"] = round(time.time() - t_start, 1)

    # 存檔：軌跡、統計、測試檔
    (run_dir / "trajectory.json").write_text(json.dumps(log, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    if TEST_FILE.exists():
        shutil.copy(TEST_FILE, run_dir / "test_cart.py")

    print("\n========== 統計 ==========")
    for k, v in stats.items():
        if k != "finish_summary":
            print(f"{k:16s} {v}")
    print(f"\n結果存在 {run_dir}")


if __name__ == "__main__":
    run_agent(sys.argv[1] if len(sys.argv) > 1 else "react")