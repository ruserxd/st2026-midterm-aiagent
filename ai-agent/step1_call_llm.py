"""步驟 1：呼叫 LLM 一次。

重點：對程式來說，LLM 只是一個「輸入文字 -> 輸出文字」的函式，
背後就是一個 HTTP POST 請求。這裡還沒有 agent。

執行：python step1_call_llm.py
"""

import time

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"   # Ollama 原生 API
MODEL = "gpt-oss:20b"


def call_llm(messages, think="low"):
    """把對話送給模型，回傳 (回答, 模型內部的思考)。

    messages 是一個 list，每一項是 {"role": ..., "content": ...}
      role = "system"    給模型的規則，例如：你是一個軟體測試高手
      role = "user"      使用者說的話
      role = "assistant" 模型之前說過的話
    """
    # 
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,          # 等整段回答完成再一次回傳，設為 True 會是一段一段的 JSON 資料
        "think": think,           # gpt-oss 的內部推理強度：low / medium / high
    }

    # 送出對 ollama 的請求
    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()

    # 解析從 ollama 得到的訊息
    msg = resp.json()["message"]
    return msg.get("content", ""), msg.get("thinking", "")


if __name__ == "__main__":
    # 實驗 1：問一個問題
    t0 = time.time()
    answer, thinking = call_llm([
        {"role": "user", "content": "我的名字是小明。請用一句話說明什麼是單元測試。"},
    ])
    print("=== 實驗 1 ===")
    print("[模型內部思考]", thinking[:300] or "(沒有回傳)")
    print("[回答]", answer)
    print(f"[耗時] {time.time() - t0:.1f} 秒\n")

    # 實驗 2：另開一次呼叫，問剛剛問過的事是否記得
    t1 = time.time()
    answer2, _ = call_llm([
        {"role": "user", "content": "我叫什麼名字？我剛剛問了你什麼？"},
    ])
    print("=== 實驗 2 ===")
    print("[回答]", answer2)
    print(f"[耗時] {time.time() - t1:.1f} 秒\n")