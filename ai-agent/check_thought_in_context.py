"""檢查：寫在 thought 參數裡的內容，下一步真的會被模型看到嗎？

做法：手動組一段歷史，裡面有一次 read_spec 呼叫，它的 thought 參數藏了一個暗號。
接著問模型「你上一步的 thought 寫了什麼暗號？」
  - 答得出暗號  -> thought 確實隨工具呼叫留在上下文中
  - 答不出來    -> Ollama 送給模型時把 thought 丟掉了，ReAct 的設計就不成立

對照組：同樣的歷史，但 thought 不放暗號；模型應該答不出來（排除瞎猜）。

執行：python3 check_thought_in_context.py
"""

import requests

from step1_call_llm import MODEL, OLLAMA_URL
from step4_react_agent import schemas_for

SECRET = "PURPLE-ELEPHANT-42"


def ask(thought_text):
    messages = [
        {"role": "system", "content": "You are a software testing agent."},
        {"role": "user", "content": "Module under test: `cart`. Write test_cart.py."},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {
            "name": "read_spec",
            "arguments": {"thought": thought_text, "name": "parse_coupon"},
        }}]},
        {"role": "tool", "tool_name": "read_spec",
         "content": "Parse a coupon code and return its discount percent."},
        {"role": "user", "content": "Stop. Do not call any tool. In your previous tool call, "
                                    "what exactly did you write in the `thought` argument? "
                                    "Quote it word for word."},
    ]
    payload = {"model": MODEL, "messages": messages, "tools": schemas_for("react"),
               "stream": False, "think": "low", "options": {"num_ctx": 16384}}
    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()["message"].get("content", "")


if __name__ == "__main__":
    print("=== 實驗組：thought 裡藏了暗號 ===")
    a = ask(f"I need the coupon rules. The secret code is {SECRET}.")
    print(a, "\n")
    print("=== 對照組：thought 裡沒有暗號 ===")
    b = ask("I need the coupon rules.")
    print(b, "\n")
    print("結果：", "✅ thought 會留在上下文中" if SECRET in a and SECRET not in b
          else "⚠️ 沒有通過，請把輸出貼回來檢查")