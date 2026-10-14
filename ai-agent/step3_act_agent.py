"""步驟 3（原生工具呼叫版）：第一個 agent，Act 模式（只有 Action，沒有 Thought）。

和文字版的差別：不再要求模型寫 "Action 1: read_spec[cart]" 再自己解析，
而是用 Ollama 的 `tools` 參數，正式告訴模型「有哪些工具、參數是什麼」，
模型回傳結構化的 tool_calls，我們執行後用 role="tool" 把結果送回去。

    messages = [規則, 任務]
    重複：
        1. 把 messages 和 TOOL_SCHEMAS 送給 LLM   -> 模型回傳 tool_calls
        2. 讀出工具名稱與參數（已經是 dict，不用解析文字）
        3. 用 TOOLS 表找到函式並執行             -> Observation
        4. 把模型的呼叫與工具結果加回 messages   （論文的上下文 c_t）
    直到模型呼叫 finish，或步數用完。

對應論文：第 3.2 節 Baselines 的 "Act"。

執行：python3 step3_act_agent.py
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

from step1_call_llm import MODEL, OLLAMA_URL
from step2_tools import TOOLS

ROOT = Path(__file__).resolve().parent.parent      # 2026-software-midterm/
SUBJECT_DIR = ROOT / "subject"                     # cart.py 在這裡
WORKSPACE = ROOT / "workspace"                     # agent 寫的測試放這裡
TEST_FILE = WORKSPACE / "test_cart.py"

MAX_STEPS = 15          # 最多呼叫模型幾次，避免無限迴圈
NUM_CTX = 16384         # 上下文長度（token）。Ollama 預設很小，太小會默默截掉前面的內容
KEEP_THINKING = False   # 是否把模型的內部思考送回歷史。False = 每一步想完就丟


# =====================================================================
# 新增工具：寫測試、跑測試、結束
# =====================================================================
def write_tests(code):
    """把模型寫的測試程式存成 workspace/test_cart.py(write_text整份重新撰寫)。"""
    WORKSPACE.mkdir(exist_ok=True)
    TEST_FILE.write_text(code.strip() + "\n", encoding="utf-8")
    n_tests = len(re.findall(r"^\s*def test", code, re.M))
    return f"Wrote test_cart.py: {len(code.splitlines())} lines, {n_tests} test functions."


def run_tests():
    """用 pytest 執行 test_cart.py，回傳 pytest 的輸出文字。"""
    if not TEST_FILE.exists():
        return "No test file yet. Use write_tests first."
    env = dict(os.environ, PYTHONPATH=str(SUBJECT_DIR))   # 讓 `import cart` 找得到 subject/cart.py
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider",
         TEST_FILE.name],
        cwd=WORKSPACE, env=env, capture_output=True, text=True, timeout=60,
    )
    return (proc.stdout + proc.stderr).strip()[-3000:]     # 太長只留最後 3000 字


def finish(summary):
    return "Episode finished."


TOOLS["write_tests"] = write_tests
TOOLS["run_tests"] = run_tests
TOOLS["finish"] = finish


# =====================================================================
# 工具說明書（JSON Schema）：告訴模型每個工具的用途與參數
# 這就是論文的動作空間 A，只是從「寫在 prompt 裡的文字」變成「結構化的定義」
# =====================================================================
def tool(tool_name, description, **params):
    """產生一個工具定義。params 的格式是 參數名稱="參數說明"，型別一律是字串。"""
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {p: {"type": "string", "description": d} for p, d in params.items()},
                "required": list(params),
            },
        },
    }


TOOL_SCHEMAS = [
    tool("list_functions", "List the functions and classes of the module `cart` with their signatures."),
    tool("read_spec", "Show only the docstring (specification) of a function, without its code.",
         name="Function name, e.g. 'parse_coupon' or 'Cart.total'."),
    tool("read_source", "Show the implementation (source code) of a function.",
         name="Function name, e.g. 'parse_coupon' or 'Cart.total'."),
    tool("write_tests", "Write the WHOLE test file test_cart.py (replaces any previous version).",
         code="The complete content of test_cart.py."),
    tool("run_tests", "Run test_cart.py with pytest and return the output."),
    tool("finish", "Stop working.",
         summary="Every place where the module disagrees with its specification."),
]


SYSTEM_PROMPT = """You are a software testing agent. Use the tools to write a pytest test suite for the Python module `cart` and to check whether the module follows its SPECIFICATION (its docstrings).

Rules:
- The test file must use `import cart`.
- Expected values must come from the specification. The implementation may contain bugs.
- When you are done, call finish with a summary of every place where the module disagrees with its specification."""

TASK = f"Module under test: `cart`. Write test_cart.py. You have at most {MAX_STEPS} steps."


# =====================================================================
# 呼叫 LLM：多傳了 tools
# =====================================================================
def call_llm(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_SCHEMAS,               # <-- 新增：工具說明書
        "stream": False,
        "think": "low",
        "options": {"num_ctx": NUM_CTX},
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    msg = data["message"]
    return {
        "content": msg.get("content", ""),
        "thinking": msg.get("thinking", ""),
        "tool_calls": msg.get("tool_calls") or [],
        "input_tokens": data.get("prompt_eval_count", 0),
        "output_tokens": data.get("eval_count", 0),
    }


def execute(name, args):
    """執行一個工具呼叫，任何錯誤都轉成文字回報給模型（錯誤也是一種 Observation）。"""
    if name not in TOOLS:
        return f"Unknown tool '{name}'. Valid tools: {', '.join(TOOLS)}."
    try:
        return TOOLS[name](**args)
    except TypeError as exc:                         # 參數名稱或數量不對
        return f"Wrong arguments for {name}: {exc}"
    except Exception as exc:
        return f"Tool error: {type(exc).__name__}: {exc}"


# =====================================================================
# Agent 迴圈
# =====================================================================
def run_agent():
    WORKSPACE.mkdir(exist_ok=True)
    if TEST_FILE.exists():
        TEST_FILE.unlink()                           # 每次從空白開始

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": TASK},
    ]
    log, finished = [], False

    for n in range(1, MAX_STEPS + 1):
        t0 = time.time()
        try:
            reply = call_llm(messages)                                   # 1. 問模型
        except Exception as exc:
            print(f"\n[Step {n}] 呼叫模型失敗，停止：{exc}")
            log.append({"step": n, "llm_error": str(exc)})
            break

        print(f"\n===== Step {n}  ({time.time() - t0:.1f}s, "
              f"in={reply['input_tokens']} out={reply['output_tokens']} tokens) =====")
        print("[模型內部思考]", reply["thinking"][:200].replace("\n", " "))
        if reply["content"].strip():
            print("[模型文字輸出]", reply["content"].strip()[:300])

        # 把模型這一步說的話（含工具呼叫）放回歷史
        assistant_msg = {"role": "assistant", "content": reply["content"],
                         "tool_calls": reply["tool_calls"]}
        if KEEP_THINKING:
            assistant_msg["thinking"] = reply["thinking"]
        messages.append(assistant_msg)

        if not reply["tool_calls"]:                                      # 沒有呼叫任何工具
            observation = "You did not call a tool. Call exactly one of the tools."
            messages.append({"role": "user", "content": observation})
            print("[Observation]", observation)
            log.append({"step": n, **reply, "observation": observation})
            continue

        for call in reply["tool_calls"]:                                 # 通常只有一個
            name = call["function"]["name"]                              # 2. 讀出名稱與參數
            args = call["function"].get("arguments") or {}
            observation = execute(name, args)                            # 3. 執行
            messages.append({"role": "tool", "tool_name": name,          # 4. 結果放回歷史
                             "content": observation})

            shown = {k: (v[:80] + "...") if isinstance(v, str) and len(v) > 80 else v
                     for k, v in args.items()}
            print(f"[Action] {name}({json.dumps(shown, ensure_ascii=False)})")
            print("[Observation]", observation[:800])
            log.append({"step": n, **reply, "action": name, "args": args,
                        "observation": observation})
            if name == "finish":
                finished = True
                break
        if finished:
            break

    log_path = WORKSPACE / "trajectory_act.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完成：共 {n} 步，{'有' if finished else '沒有'}呼叫 finish。軌跡存在 {log_path}")
    print(f"測試檔：{TEST_FILE if TEST_FILE.exists() else '（沒有寫出測試）'}")


if __name__ == "__main__":
    run_agent()