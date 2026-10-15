"""檢查 v2：放回歷史的 thinking 有沒有真的被放進 prompt？——用 token 數直接量。

上一版（check_thinking_in_context.py）要求模型「逐字引用」自己的推理。但模型可能
被訓練成不公開推理內容，所以「引用不出來」不一定代表「看不到」。

這一版不靠模型回答，只看 Ollama 回傳的 prompt_eval_count（這次送進模型的 token 數）：
  同一段歷史，一次在 thinking 放入約 300 token 的長文字，一次留空。
  - token 數多出約 300 -> thinking 有被放進 prompt
  - token 數幾乎相同  -> thinking 被丟掉了

和上一版一樣測兩種位置：
  A：歷史後面再接一則新的 user 訊息（thinking 位於最後一則 user 訊息之前）
  B：歷史以工具結果結尾（thinking 位於最後一則 user 訊息之後，和 agent 實際流程相同）

注意：Ollama 會重用前一次請求相同開頭的快取，被重用的部分不計入 prompt_eval_count。
所以每次請求都在 system 訊息開頭放一個隨機字串，讓快取無法重用。

執行：python3 check_thinking_tokens.py
"""

import uuid

import requests

from step1_call_llm import MODEL, OLLAMA_URL
from step3_act_agent import TOOL_SCHEMAS

LONG_THINKING = " ".join(["I need to read the coupon rules carefully before writing any test."] * 25)


def prompt_tokens(thinking_text, with_extra_user_message):
    nonce = uuid.uuid4().hex                       # 讓 Ollama 無法重用快取
    messages = [
        {"role": "system", "content": f"[{nonce}] You are a software testing agent."},
        {"role": "user", "content": "Module under test: `cart`. Write test_cart.py."},
        {"role": "assistant", "content": "", "thinking": thinking_text,
         "tool_calls": [{"function": {"name": "read_spec", "arguments": {"name": "parse_coupon"}}}]},
        {"role": "tool", "tool_name": "read_spec",
         "content": "Parse a coupon code and return its discount percent."},
    ]
    if with_extra_user_message:
        messages.append({"role": "user", "content": "Continue."})
    payload = {"model": MODEL, "messages": messages, "tools": TOOL_SCHEMAS, "stream": False,
               "think": "low", "options": {"num_ctx": 16384, "num_predict": 1}}
    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json().get("prompt_eval_count", 0)


if __name__ == "__main__":
    for label, extra_user in [("位置 A：歷史後面再接一則 user 訊息", True),
                              ("位置 B：歷史以工具結果結尾（同 agent 流程）", False)]:
        with_t = prompt_tokens(LONG_THINKING, extra_user)
        empty_t = prompt_tokens("", extra_user)
        diff = with_t - empty_t
        print(f"===== {label} =====")
        print(f"thinking 放長文字：{with_t} tokens")
        print(f"thinking 留空    ：{empty_t} tokens")
        print(f"差異             ：{diff:+d} tokens")
        print("結果：", "✅ thinking 有被放進 prompt" if diff > 100 else "❌ thinking 被丟掉了", "\n")