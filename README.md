# ReAct 測試生成 Agent：完整實驗紀錄

> **研究問題**：把 ReAct 論文（Yao et al., ICLR 2023）的核心消融實驗「ReAct vs Act」搬到**單元測試生成**。要求 agent 把推理寫進上下文（Thought），能不能讓它找到更多 bug、寫出更少錯誤的測試、減少 assertion echo？
>
> **主要結果**（5 個條件 × 100 次，共 500 次）
> - **few-shot 範例的影響遠大於 Thought**：抓到的 bug +0.83 個、誤報 −55%（p < 0.001）。
> - **Thought 本身沒有幫助**；沒有範例時，agent 反而讀得更少（4.6 → 3.1 份規格，p < 0.001），並且總是增加成本。
> - 論文「ReAct 優於 Act」的主張，在本設定（小型推理模型、原生工具呼叫、測試生成）下**未被重現**。

---

## 目錄

1. [實驗總覽](#1-實驗總覽)
2. [實驗環境](#2-實驗環境)
3. [步驟 1：呼叫 LLM](#3-步驟-1呼叫-llm)
4. [步驟 2：工具（環境）](#4-步驟-2工具環境)
5. [步驟 3：Act agent](#5-步驟-3act-agent)
6. [步驟 4：加入 Thought（ReAct）](#6-步驟-4加入-thoughtreact)
7. [步驟 5：few-shot 範例](#7-步驟-5few-shot-範例)
8. [步驟 6：最終版 agent](#8-步驟-6最終版-agent)
9. [步驟 7：獨立評分](#9-步驟-7獨立評分)
10. [步驟 8：正式實驗](#10-步驟-8正式實驗)
11. [Threats to validity](#11-threats-to-validity)
12. [工程上遇到的問題](#12-工程上遇到的問題)
13. [待辦與後續](#13-待辦與後續)

---

## 1. 實驗總覽

### 1.1 被測程式與植入的 bug

被測程式 `cart.py` 是一個約 160 行的購物車計價模組，規格寫在 docstring 中。我先寫好正確版，再植入 4 個 bug。agent 只拿得到含 bug 的版本，也不知道 bug 在哪裡。

| ID | 函式 | 內容 | 類型 |
|---|---|---|---|
| B1 | `bulk_discount_percent` | 剛好 50 件應打 10% 折扣，程式給 5%（`>=` 寫成 `>`） | 邊界 |
| B2 | `parse_coupon` | 規格不分大小寫，程式分大小寫（少了 `.upper()`） | 規格功能 |
| B3 | `Cart.remove_item` | 數量歸零後商品未被移除（`<=` 寫成 `<`） | 狀態 |
| B4 | `Cart.total` | 運費應以套用優惠碼「後」的金額計算，程式用「前」的金額 | 多跳 |

B4 需要串連 `total`、`parse_coupon`、`shipping_fee` 三份規格才能發現，對應論文 HotpotQA 的多跳推理。

### 1.2 五個實驗條件

| 條件 | Thought | few-shot 範例 | 告訴步數上限 | 對應論文 |
|---|:---:|:---:|:---:|---|
| `act` | — | — | — | Act baseline |
| `react` | ✓ | — | — | ReAct（Â = A ∪ L） |
| `act+fewshot` | — | ✓（刪除 Thought 行） | — | 附錄 C 的 Act prompt |
| `react+fewshot` | ✓ | ✓ | — | 附錄 C 的 ReAct prompt |
| `react+fewshot+limit` | ✓ | ✓ | ✓ | 額外假設（F10） |

### 1.3 獨立量尺

不採信 agent 的自我回報。每份測試檔都跑在 6 個版本的 cart 上（正確版、全 bug 版、4 個單一 bug 版），自動判定：

- 抓到哪些 bug（bug-revealing）
- 哪些測試照抄了 bug 的行為（assertion echo）
- 哪些測試本身是錯的（invalid，即誤報）
- line / branch coverage

詳見[步驟7](#9-步驟-7獨立評分)。

---

## 2. 實驗環境

| 項目 | 設定 |
|---|---|
| Ollama 版本 | `0.30.7` |
| 模型 | `gpt-oss:20b` |
| 推理強度 | `think = "low"，因為 gpt-oss 內部模型就會推理` |
| 上下文長度 | `num_ctx = 16384` |
| 內部思考是否送回歷史 | 否（`KEEP_THINKING = False`） |
| 最大步數 | 步驟 3–5：15；步驟 6 起（正式實驗）：25 |
| 溫度 | 未設定（使用 Ollama 預設值） |

### 資料夾結構

```text
2026-software-midterm/
├── .venv/
├── ai-agent/
│   ├── step1_call_llm.py        呼叫 LLM
│   ├── step2_tools.py           工具（環境）：list_functions、read_spec、read_source
│   ├── step3_act_agent.py       Act agent（原生工具呼叫版）
│   ├── step4_react_agent.py     ReAct / Act 共用（參數切換模式）
│   ├── step5_fewshot_agent.py   加上 few-shot 範例
│   ├── step6_agent.py           最終版 agent：結束條件、重試、所有條件參數化
│   ├── step7_evaluate.py        獨立評分
│   └── step8_experiment.py      批次執行、彙整、排列檢定
├── subject/
│   └── cart.py                  被測程式（含植入 bug）
├── evaluation/                  評分用（agent 看不到）：正確版、bug 定義、參考測試
├── workspace/                   agent 執行中的工作區
└── runs/
    ├── react_*/  act_*/         步驟 4 的單次執行
    ├── fewshot/                 步驟 5 的單次執行
    ├── exp/                     步驟 6 的試跑
    ├── final_attempt1/          步驟 8 第一批（9/25 次因格式錯誤中斷，保留作為可靠性證據）
    ├── final/                   步驟 8 前導實驗（每條件 n = 5）
    └── final_n100/              步驟 8 正式實驗（每條件 n = 100）
```

---

## 3. 步驟 1：呼叫 LLM

**目的**：確認 LLM 對程式來說只是「輸入文字 → 輸出文字」的函式，背後就是一個 HTTP POST 請求。問句使用英文，與之後 agent 的 system prompt、規格（docstring）、工具說明一致。

```python
payload = {
    "model": "gpt-oss:20b",
    "messages": messages,   # 對話歷史：system / user / assistant
    "stream": False,
    "think": "low",         # gpt-oss 的內部推理強度
}
resp = requests.post("http://localhost:11434/api/chat", json=payload)
```

| 實驗 | 送出的訊息 | 內部思考（thinking） | 回答 |
|---|---|---|---|
| 1 | `My name is Ming. In one sentence, what is a unit test?` | `Need concise definition.` | 一句話的單元測試定義 |
| 2（另開一次呼叫） | `What is my name? What did I just ask you?` | `Need to answer: can't know your name; user asked "What is my name?" and "What did I just ask you?"` | 不知道名字；只列出這次的兩個問題 |

**發現**
- **LLM 沒有記憶**：實驗 2 的內部思考只列出這次的兩個問題，完全沒提到上一次呼叫的「Ming」或「單元測試」，表示模型不是不說，而是真的看不到。因此 agent 每一步都必須重送整段歷史（論文的上下文 cₜ）。
- **內部思考不會留下來**：`thinking` 只存在於這次的回覆中，不在 messages 裡，下一次呼叫就消失。之後的實驗固定不把它送回歷史（`KEEP_THINKING = False`）。
- **輸出具有隨機性**：同樣的問題重跑一次，回答的用詞與長度都不同；這是正式實驗每個條件要跑多次的原因。
- **單次耗時參考價值低**：同一個問題，兩次執行分別為 4.2 秒與 0.5 秒（第一次可能需要載入模型）。成本以步驟 8 多次執行的平均值為準。

## 4. 步驟 2：工具（環境）

**目的**：工具就是「輸入字串 → 輸出字串」的普通函式；`TOOLS` 字典的 key 就是論文的動作空間 A。

| 工具 | 回傳內容 | 對應論文 |
|---|---|---|
| `list_functions` | 函式與參數清單 | 類似 `search` |
| `read_spec` | 只有 docstring（規格） | 類似 `search` |
| `read_source` | 實作程式碼 | 類似 `lookup` |

把 `read_spec` 與 `read_source` 分開，是為了觀察期望值的來源：

| 期望值來源 | 對 `parse_coupon("save10")` 寫出的測試 | 結果 |
|---|---|---|
| 規格（`read_spec`） | `== 10` | 測試失敗，**抓到 bug** |
| 程式現有輸出（`read_source` 或直接執行） | `raises ValueError` | 測試通過，**bug 被藏起來（assertion echo）** |

---

## 5. 步驟 3：Act agent

**目的**：把 LLM 和工具接成迴圈：模型選工具 → 程式執行 → 結果放回歷史 → 再問模型，直到 `finish`。

### 5.1 工具要用 Ollama 規範的格式定義

最初仿照論文，用文字格式 `Action n: name[arg]` 讓模型輸出動作，結果模型回應空白或出現 HTTP 500。原因是 gpt-oss 訓練時就內建了**原生工具呼叫**：它看到動作清單，就改用自己的格式呼叫工具，與文字協定衝突。

因此改為依照 Ollama 規範，在 `/api/chat` 的 `tools` 參數中，用 JSON Schema 定義每個工具：

```python
{
    "type": "function",
    "function": {
        "name": "read_spec",
        "description": "Show only the docstring (specification) of a function.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "e.g. 'Cart.total'"}},
            "required": ["name"],
        },
    },
}
```

| 論文概念 | 實作 |
|---|---|
| 動作空間 A | `tools` 參數中的 6 個工具：`list_functions`、`read_spec`、`read_source`、`write_tests`、`run_tests`、`finish` |
| Action | 模型回傳的 `message.tool_calls`（參數已是 dict，不需自己解析） |
| Observation | `{"role": "tool", "tool_name": ..., "content": 結果}` 附加回 messages |

### 5.2 Agent 迴圈（精簡版）

```python
messages = [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": TASK}]
for step in range(MAX_STEPS):
    reply = call_llm(messages, TOOL_SCHEMAS)                 # 1. 問模型
    messages.append({"role": "assistant", "tool_calls": reply["tool_calls"]})
    for call in reply["tool_calls"]:
        name, args = call["function"]["name"], call["function"]["arguments"]
        observation = TOOLS[name](**args)                     # 2. 執行工具
        messages.append({"role": "tool", "tool_name": name,   # 3. 結果放回歷史
                         "content": observation})
        if name == "finish":
            break
```

### 5.3 執行結果

- **Run 1（路徑設定錯誤，不列入數據）**：工具全部回傳 `FileNotFoundError`，暴露了幾種失敗模式：沒讀到資料就猜測寫測試（幻覺）、同一個呼叫重複 6 次（迴圈）、不會換策略。
- **Run 2（Act 基準線）**：10 步、約 14 秒；讀 5 份規格、0 次讀程式碼，寫一次、跑一次就結束，找到 2 個不符規格處（bulk 邊界、優惠碼大小寫）。弱點是沒有迭代，而且把大小寫和空白混在同一個輸入，以致診斷不精確。

---

## 6. 步驟 4：加入 Thought（ReAct）

### 6.1 設計

論文第 2 節：**Â = A ∪ L**。Thought 不影響環境，但會寫進上下文，供後續推理使用。

做法：**ReAct 模式下，每個工具多一個必填參數 `thought`**。

```python
def schemas_for(mode):
    if mode == "act":
        return TOOL_SCHEMAS
    schemas = copy.deepcopy(TOOL_SCHEMAS)
    for s in schemas:
        params = s["function"]["parameters"]
        params["properties"] = {"thought": {"type": "string", "description": THOUGHT_DESC},
                                **params["properties"]}
        params["required"] = ["thought"] + params["required"]
    return schemas
```

執行工具前先把 `thought` 取出，所以它**不影響環境**；但它是工具呼叫的一部分，會**留在歷史裡**，之後每一步都看得到：

```python
args = dict(call["function"]["arguments"])
thought = args.pop("thought", None)      # Thought 不傳給工具
observation = TOOLS[name](**args)
```

對比：gpt-oss 的內部思考想完就丟（`KEEP_THINKING = False`）。

**控制變因**：兩種模式只差兩處。

| | Act | ReAct |
|---|---|---|
| 工具 | 6 個 | 同樣 6 個，各多一個 `thought` 參數 |
| system prompt | 規則 | 規則 + 一句：「Every tool has a `thought` argument. Before each action, use it to reason about the current situation.」（取自論文 HotpotQA prompt 的說法） |
| 其他設定 | 相同 | 相同 |

刻意不告訴模型「該想什麼」，避免改進其實來自指示本身。

### 6.2 結果（各 1 次，同一支程式）

| 指標 | Act | ReAct |
|---|---:|---:|
| 步數 | 10 | 10 |
| 讀了幾份規格 | 5 | 6（多 `Cart.subtotal`） |
| 寫 / 跑測試次數 | 1 / 1 | 1 / 1 |
| 測試失敗數 | 多個（輸出被截斷） | 4 / 40 |
| 真正抓到的問題 | 2 | 2 |
| **誤報** | 0 | **1** |
| 不呼叫工具 | 1 | 0 |
| 漏寫 thought | — | 0 |
| 輸入 / 輸出 token | 13,621 / 1,836 | 13,957 / 1,653 |
| 內部思考 / Thought 字元數 | 346 / 0 | 372 / 353 |
| 耗時 | 17.9 秒 | 18.0 秒 |

ReAct 第 1 步的輸入 token 為 616（Act 為 419），多出的約 200 token 是 `thought` 參數說明的固定成本。

### 6.3 發現

**F1：Thought 淪為「動作標籤」。** 第 2–7 步的 Thought 是 `Spec of apply_discount.`、`Spec of parse_coupon.`……，只複述動作，既不解讀觀察，也不規劃。平均約 35 字元。第 10 步的對照尤其明顯：

| 內部思考（會被丟棄） | Thought（會被保留） |
|---|---|
| `Discrepancies: bulk_discount_percent 50 should be 10 but returns 5 => bug. parse_coupon case-insensitive fails...` | `Final summary of mismatches.` |

→ 推理模型會遵守 Thought 的格式，但**真正的推理留在內部**。「要求寫 Thought」不等於「得到推理」。

**F2：ReAct 產生幻覺 API 與誤報。** ReAct 沒讀 `Cart.items` 的規格，卻假設它回傳字典串列：

```python
assert any(item["name"] == "widget" and item["quantity"] == 2 for item in c.items())
```

規格其實是 `Return a new dict {name: quantity}`。測試因 `TypeError` 失敗，finish 摘要因此誤報「items() 回傳格式錯誤」。連鎖效應是：這個測試的後半段原本能揭露 `remove_item` 的真實 bug，卻被前半段的錯誤蓋過。
→ 對應論文 Table 2 的幻覺；Thought 中沒有出現「這份規格還沒讀」之類的進度追蹤。

**F3：讀了多跳規格，卻沒有寫出有區分力的測試。** 兩種模式都讀了 `Cart.total`（運費以套用優惠碼後的金額計算）。ReAct 的測試用 150 元、SAVE10：優惠前後都低於免運門檻 1000，不論哪種算法，運費都是 60，所以無法區分。
需要的是「優惠前 ≥ 1000、優惠後 < 1000」的輸入（例如 1100 元、SAVE20），也就是串連三份規格的邊界值分析。

**F4：Act 的內部思考出現 assertion echo 的衝動。** Act 第 9 步的內部思考：

> We need adjust tests to match implementation. But we should just report mismatches.

測試失敗後，模型的第一反應是修改測試去配合程式；是 system prompt 的規則（期望值必須來自規格）把它拉回來。

**F5：測試設計瑕疵。**
- ReAct：`("SAVE0", None)` 搭配 `if expected is not None`，這個測試案例**什麼都沒驗證**。
- ReAct：`"  Save50 "` 同時混合大小寫與空白，摘要因此誤稱「空白也不支援」。
- 正面：兩邊都有只測大小寫的乾淨案例（Act：`"SaVe1"`；ReAct：`"save25"`）。

**F6：兩種模式都沒有迭代。** 都是讀規格 → 寫一次 → 跑一次 → 結束。

### 6.4 小結

n = 1 時，**看不出 Thought 有幫助**：ReAct 多讀一份規格，但多了一個誤報。內部思考字數相近（346 對 372），沒有證據顯示 Act 會在內部多想來補償。
論文的 Thought 品質來自 **few-shot 範例**（附錄 C），而我們還沒有提供範例 → 這是步驟 5 的動機。

> **環境問題**：上層資料夾的 pytest 設定含 `--cov=subject`，使 `run_tests` 的輸出夾雜 coverage 警告，浪費 token，也讓 Act 的失敗清單被截斷。修正方式是在 pytest 參數加上 `-o addopts=`（清空設定檔的預設參數）。


### 6.5 驗證：推理會不會留在上下文中

| 檢查 | 方法 | 結果 |
|---|---|---|
| `thought` 參數 | 暗號藏在 thought，要求模型逐字引用 | ✅ 逐字引用出暗號 |
| `thinking`（最後一則 user 訊息之前） | 比較 thinking 放長文字 vs 留空時的輸入 token 數 | ❌ 差 −5 token，被丟掉 |
| `thinking`（最後一則 user 訊息之後，同 agent 流程） | 同上 | ✅ 多出 330 token，有放進 prompt |

- 依 Ollama 的 gpt-oss 樣板，歷史中的 thinking 只有在「最後一則 user 訊息之後」才會放進 prompt（`Show thinking only after last user message`）。
- 暗號測試中，即使 thinking 確實在 prompt 裡，模型被要求逐字引用時仍會**編造**一段推理。第一次判斷因此誤以為 thinking 沒有送進模型，改用 token 數這種獨立量尺才得到正確答案。→ 模型對自己推理的說明不能直接採信（同 F8）。
- 正式實驗的 500 次都設定 `KEEP_THINKING = False`；保留內部思考的效果另以 `act+keep`、`react+keep` 延伸實驗檢驗。
---

## 7. 步驟 5：few-shot 範例

### 7.1 設計

論文附錄 C：ReAct 的 prompt 附有人工撰寫的完整軌跡，模型靠模仿範例寫出好的 Thought。

- 範例使用**另一個模組 `thermo`**（`c_to_f`、`classify`、`Log`），避免洩漏 cart 的答案；其中植入 1 個 bug（`classify(25)` 回傳 `"mild"`）。
- 範例中的 Observation 是**實際執行工具**得到的輸出。
- 範例刻意示範論文第 2 節的 Thought 類型：擬定計畫、追蹤進度（`Still unread: ...`）、避免猜測（`I must not guess what latest() returns.`）、擷取重點（邊界值）、判斷失敗原因（測試寫錯 vs 程式違反規格）。
- 第一次跑測試出現兩個失敗：`c_to_f(36.6)` 是**測試寫錯**（忽略了四捨五入）→ 修正測試；`classify(25)` 是**程式違反規格** → 保留測試。

範例中最關鍵的一步：

```text
Thought: Two failures. (1) c_to_f(36.6): 36.6 * 9 / 5 + 32 = 97.88, but the spec says
round to 1 decimal, so the correct value is 97.9. MY expected value was wrong, so I fix
the test. (2) classify(25) returned 'mild', but the spec says celsius >= 25 is 'hot'.
That expected value comes from the spec, so the MODULE is wrong; I keep this test unchanged.
```

**Act 拿到同一條範例，但刪除所有 Thought 行**，與論文 Act baseline 的做法一致：

```python
def strip_thoughts(text):
    return "\n".join(line for line in text.splitlines() if not line.startswith("Thought: "))
```

範例以文字形式放在 system prompt 中，使 prompt 增加約 1,300～1,700 token，而且**每一步都要重送**。

### 7.2 結果（各 1 次）

| 指標 | Act + 範例 | ReAct + 範例 |
|---|---:|---:|
| 步數 | 11 | 15（用完上限） |
| 讀了幾份規格 | 5 | 7（含 `add_item`、`remove_item`） |
| 寫 / 跑次數 | 1 / 1 | 2 / 2 |
| 不呼叫工具 | 2 | 2 |
| 輸入 / 輸出 token | 28,990 / 1,949 | 59,681 / 3,282 |
| Thought 字元數 | — | 410（平均約 31） |
| 耗時 | 15.3 秒 | 31.0 秒 |

### 7.3 發現

**F7：模仿了範例的「動作」，沒有模仿「推理」。** ReAct 的 Thought 仍是 `Read spec.`、`Run tests again.`；範例中的 `Still unread`、`I must not guess` 完全沒出現。

**F8：儀式性的迭代與不忠實的 Thought。** 兩版測試檔的差異**只有註解**，斷言完全沒變，兩次 `run_tests` 都是 7 個失敗。但 Thought 宣稱：

> Updated tests to match spec: bulk_discount_percent values, parse_coupon case handling, items structure, remove_item entire removal.

→ Thought 可能與實際行動不符；論文所說的「可解釋性」要打折扣。

**F9：ReAct 首次抓到 `remove_item` 的 bug。** `assert 'grape' not in {'grape': 0}` 失敗，原因是這次讀了 `remove_item` 的規格。

**F10：`items()` 的幻覺系統性出現。** 所有執行都沒有讀過 `Cart.items` 的規格，各自猜了不同的回傳格式：

| 執行 | 猜測 |
|---|---|
| 步驟 4 ReAct | `[{"name": ..., "quantity": ...}]` |
| 步驟 5 ReAct | `{"apple": (2.5, 3)}` |
| 步驟 5 Act | `{"apple": (1.0, 3)}` |

規格為 `{name: quantity}`。假設：任務訊息寫著「at most 15 steps」，模型為了省步數只讀 5～7 份規格，而排在清單最後的 `items`、`subtotal`、`total` 總是被略過。

**F11：沒讀規格卻說「規格不清楚」，而且猜測的規則恰好等於 bug 的行為。** ReAct 第一版測試的註解：

```python
# Coupon SAVE20 => 20% off of subtotal before shipping? spec unclear, ...
expected_total = final_after_coupon + cart.shipping_fee(120.0)
```

它沒讀過 `Cart.total`，就猜成「運費用優惠前金額計算」，這正是植入的 bug 行為。本例金額沒有跨過免運門檻，所以沒有造成影響；如果輸入是 1,100 元，就會成為 assertion echo。

**F12：Act 只模仿了一半。** Act 讀了 5 份規格、沒有迭代，還多了一個誤讀規格的測試：`shipping_fee(1500, member=True)` 期望 30（規格：滿 1000 元免運，不分會員）。

### 7.4 小結

範例 + Thought 讓 ReAct 讀得比較多、抓到比較多 bug，但錯誤的測試也比較多，成本約為 Act 的 2 倍，而且 Thought 仍然很淺，甚至與行動不符。這些都只是 1 次的結果，不能當作結論。
手動判讀已經成為瓶頸（而且曾經誤判 echo）→ 先進行步驟 7 的自動評分。

---

## 8. 步驟 6：最終版 agent

### 8.1 處理前面觀察到的失敗模式

前面觀察到的失敗模式會干擾比較，因此在正式實驗前先處理；**兩種模式套用完全相同的規則**，避免處理方式本身成為變因。

| 觀察到的問題 | 出現在 | 處理方式 |
|---|---|---|
| 步數上限 15，ReAct + 範例剛好用完 | 步驟 5 | 上限提高到 25 |
| 「at most 15 steps」可能讓模型少讀規格 | F10 假設 | 預設不告訴模型上限；另設 `+limit` 條件檢驗 |
| 只講話、不呼叫工具 | 每一輪 | 提醒；連續 3 次即結束（`no_tool_calls`） |
| 重複同一個呼叫 | 步驟 3 Run 1 | 照常執行並附註提醒；連續 3 次即結束（`loop`） |
| 重寫測試只改註解 | F8 | 不干預，只記錄（`noop_rewrites`，以 AST 比較，忽略註解） |
| 格式錯誤的工具呼叫（HTTP 500） | 步驟 8 第一批 | 同一請求重試最多 3 次；仍失敗就告知模型格式錯誤；連續 3 步才結束（`llm_error`） |

重試的核心程式：

```python
for attempt in range(MAX_LLM_ATTEMPTS):      # 最多 3 次
    try:
        reply = call_llm(messages, schemas)
        break
    except Exception as exc:
        stats["llm_retries"] += 1
        time.sleep(2)
```

每次執行都會記錄 `stop_reason`：`finish`、`step_limit`、`no_tool_calls`、`loop`、`llm_error`。

### 8.2 試跑觀察（各 1 次）

- 不告訴步數上限時，ReAct + 範例讀了 10 份規格（步驟 5 是 7 份），而且第一次出現 **act to reason**：跑完測試、看到失敗後，回頭讀了 `Cart.total` 與 `Cart.subtotal` 的規格，再重寫測試。
- 它讀到 `Cart` 類別的說明：`A shopping cart holding items as name -> (unit_price, quantity).` 這句描述的是內部儲存方式，和 `items()` 回傳的 `{name: quantity}` 不同，可能誘發 F10 的錯誤猜測。決定**保留**這個規格瑕疵（真實的規格也常混雜內部細節），列入 threats to validity。
- 同一個條件前後兩次的結果不同（3/4 → 2/4），顯示單次執行的參考價值很低。

---

## 9. 步驟 7：獨立評分

### 9.1 方法

把同一份 `test_cart.py` 分別跑在 6 個版本的 cart 上：

| 版本 | 內容 |
|---|---|
| `fixed` | 正確版（規格的標準答案） |
| `buggy` | 含 4 個 bug（即 `subject/cart.py`） |
| `B1`～`B4` | 各只含 1 個 bug |

依照每個測試在各版本上的結果分類：

| 分類 | 在 fixed 上 | 在 bug 版上 | 意義 |
|---|---|---|---|
| bug-revealing | 通過 | 某個版本**失敗**（`failed`） | 抓到 bug |
| passing | 通過 | 全部通過 | 正確，但沒抓到 bug |
| assertion-echo | 失敗 | 某個版本通過 | 期望值照抄了 bug 的行為 |
| invalid | 失敗 | 全部失敗 | 期望值錯誤（誤報） |
| collection-error | 無法載入 | — | 測試檔本身無法載入（例如語法錯誤） |
| skipped | 略過 | — | 不列入判斷 |

兩種特殊情況：

- **`combined`（多個 bug 同時存在）**：某個測試在 B1～B4 單一 bug 版上的結果都和 fixed 相同，只在 `buggy`（4 個 bug 同時存在）上不同，代表它抓到或照抄的是 bug 之間的交互作用。這種情況仍歸類為 bug-revealing 或 assertion-echo，但標記為 `combined`，不計入「抓到的 bug（/4）」。
- **只在 bug 版無法載入的測試檔**：有些測試檔會在模組層級呼叫 cart（例如在 import 時執行 `parse_coupon("save10")`），所以在 fixed 上可以載入，在 B2 版卻因例外而整份無法載入。此時只用 `<collection error>` 這一列，以**檔案層級**記為抓到該 bug；該版本上沒有結果（`missing`）的個別測試**不算**失敗。

```python
def classify(outcomes, test):
    if test == "<collection error>":
        if outcomes["fixed"].get(test) == "error":
            return "collection-error", []
        broken = [b for b in BUG_IDS if outcomes[b].get(test) == "error"] or ["combined"]
        return "bug-revealing", broken                  # 只在 bug 版無法載入：檔案層級
    on_fixed = outcomes["fixed"].get(test, "missing")
    if on_fixed == "skipped":
        return "skipped", []
    on_buggy = outcomes["buggy"].get(test, "missing")
    if on_fixed == "passed":
        reveals = [b for b in BUG_IDS if outcomes[b].get(test) == "failed"]   # missing 不算失敗
        if reveals:
            return "bug-revealing", reveals
        if on_buggy == "failed":
            return "bug-revealing", ["combined"]
        return "passing", []
    echoes = [b for b in BUG_IDS if outcomes[b].get(test) == "passed"]
    if echoes:
        return "assertion-echo", echoes
    if on_buggy == "passed":
        return "assertion-echo", ["combined"]
    return "invalid", []
```

另外以 coverage.py 量測測試在 fixed 上的 line / branch coverage。

> **量尺修正（2026-10-15）**：初版用 `!= "passed"` 判斷失敗，而且沒有檢查 `buggy` 版。測試檔只在 bug 版無法載入時，該版本上的每個測試都是 `missing`，結果全部被算成 bug-revealing。n = 100 中有 8 次執行受影響，revealing 測試數被高估（最大值 30、31 即由此而來），「抓到的 bug」幾乎不變（差 ≤ 0.03）。`combined` 的情況在 n = 100 中為 0 次。詳見 [REVIEW.md](REVIEW.md)。§10 的數據需以修正後的量尺重新評分。

### 9.2 量尺驗證

量尺要先驗證過，才能拿來量東西：

- 人工依規格撰寫的參考測試：4/4 bug、0 echo、0 invalid、line / branch coverage 100%。
- 8 個已知分類的測試全部判斷正確：B1–B4 各一個 echo，以及一個 B1 + B4 同時存在時才成立的 `combined` echo（`test_echo_combined_b1_b4`：50 件 × 22 元、SAVE10，正確為 951，只有 B1 為 1000.5，只有 B4 為 951，B1 + B4 為 940.5）。
- 執行方式：`python3 step7_evaluate.py --selftest`，只使用 `evaluation/` 底下的檔案，不會寫入 `runs/`。
- 檢查 `subject/cart.py` 是否與「正確版 + 全部 bug」一致；曾因檔尾少一個換行而觸發警告（不影響行為）。

### 9.3 重新評分前導執行

| 條件（來源） | 抓到的 bug | revealing | echo | invalid | line % | branch % |
|---|---|---:|---:|---:|---:|---:|
| Act（步驟 4） | 2/4（B1、B2） | 4 | 0 | 1 | 89.3 | 84.1 |
| ReAct（步驟 4） | 2/4（B1、B2） | 3 | 0 | 1 | 89.3 | 81.8 |
| Act + 範例（步驟 5） | 3/4（B1、B2、B3） | 4 | 0 | 5 | 93.3 | 88.6 |
| ReAct + 範例（步驟 5） | 3/4（B1、B2、B3） | 4 | 0 | 3 | 93.3 | 88.6 |

> **更正**：先前手動判讀為「Act + 範例只抓到 2 個 bug、誤報 ≥ 2」，自動評分顯示實際是 3 個 bug、5 個誤報。手動判讀也曾誤判一次 echo。→ 這說明了獨立量尺的必要性。

---

## 10. 步驟 8：正式實驗

### 10.1 設計

- 五個條件**輪流執行**（交錯），讓伺服器負載等時間因素平均分散到每個條件。
- 每次執行完立即評分，不採信 agent 的自我回報。
- **四個比較在看到 n = 100 的結果之前即已決定**：Thought（無範例）、Thought（有範例）、範例、告訴上限。
- 統計方法：排列檢定（雙尾、10,000 次、固定 seed）。

```python
def permutation_p(a, b, n_perm=10000, seed=0):
    rng = random.Random(seed)
    observed = abs(mean(b) - mean(a))
    pooled, hits = a + b, 0
    for _ in range(n_perm):
        rng.shuffle(pooled)                                   # 隨機重新分組
        diff = abs(mean(pooled[len(a):]) - mean(pooled[:len(a)]))
        hits += diff >= observed
    return (hits + 1) / (n_perm + 1)
```

### 10.2 第一批（`final_attempt1`）：可靠性問題

25 次中有 **9 次以 `llm_error` 中斷**，全部是 `HTTP 500: error parsing tool call`：

| 情況 | 次數 |
|---|---:|
| 呼叫 `write_tests` 時出錯（長段程式碼塞進 JSON 字串，跳脫字元出錯） | 8 / 9 |
| JSON 前面先寫了一段文字（推理漏進參數） | 2 / 9 |
| JSON 後面多一個字元（`{"thought": "..."})`） | 1 / 9 |

第 4 輪有 4 個條件連續失敗。中斷的執行會被算成 0 個 bug，使平均值失真（react 5 次中有 3 次中斷，平均只有 0.4）。
→ 加入重試機制後重跑。**原生工具呼叫在傳遞長段程式碼時特別脆弱。**

### 10.3 前導實驗（`final`，每條件 n = 5）

25 次全部 `finish`；共發生 5 次格式錯誤，重試後全部恢復。

| 條件 | 抓到的 bug | B3 | B4 | invalid | 讀了幾份規格 | 輸入 token |
|---|---|---:|---:|---:|---:|---:|
| `act` | 1.8 [0–3] | 1/5 | 0/5 | 1.2 | 6.0 | 31.8k |
| `react` | 1.6 [0–2] | 0/5 | 0/5 | 4.2 | 3.6 | 28.5k |
| `act+fewshot` | 2.8 [2–4] | 2/5 | 2/5 | 1.0 | 8.2 | 38.6k |
| `react+fewshot` | 2.8 [2–3] | 3/5 | 1/5 | 1.8 | 8.0 | 47.9k |
| `react+fewshot+limit` | 2.6 [2–3] | 2/5 | 1/5 | 0.4 | 8.2 | 60.5k |

n = 5 只看得出大的差異（範例），無法判斷 Thought 的效果 → 擴大到 n = 100。

### 10.4 正式實驗（`final_n100`，每條件 n = 100）

共 500 次，耗時 190.2 分鐘；494 次 `finish`、2 次 `loop`、4 次 `step_limit`，**0 次 `llm_error`**。

格式：平均 [最小–最大]；「k/n」代表 n 次執行中有 k 次。

**(a) 測試品質**

| 指標 | act | react | act+fewshot | react+fewshot | +limit |
|---|---|---|---|---|---|
| **抓到的 bug（/4）** | 1.8 [0–4] | **1.4** [0–3] | 2.4 [0–4] | **2.5** [0–4] | 2.4 [0–4] |
| B1 邊界 | 72/100 | 61/100 | 87/100 | 88/100 | 88/100 |
| B2 大小寫 | 77/100 | 70/100 | 93/100 | 89/100 | 92/100 |
| B3 移除商品 | 23/100 | 11/100 | 53/100 | 67/100 | 61/100 |
| B4 運費順序（多跳） | 4/100 | 3/100 | 4/100 | 7/100 | 2/100 |
| 測試數 | 23.8 [1–49] | 21.1 [0–44] | 35.4 [1–53] | 33.5 [0–53] | 34.1 [0–55] |
| bug-revealing 測試 | 2.2 [0–5] | 1.7 [0–16] | 3.8 [0–30] | 3.7 [0–31] | 3.1 [0–22] |
| assertion-echo 測試 | 0.1 [0–1] | 0.1 [0–3] | 0.1 [0–2] | 0.1 [0–1] | 0.0 [0–1] |
| **invalid 測試（誤報）** | 2.8 [0–12] | 3.2 [0–17] | 1.4 [0–6] | 1.3 [0–6] | 1.0 [0–5] |
| line coverage % | 82.7 | 82.7 | 91.3 | 93.8 | 93.6 |
| branch coverage % | 74.4 | 73.6 | 86.2 | 90.2 | 90.2 |

**(b) agent 行為**

| 指標 | act | react | act+fewshot | react+fewshot | +limit |
|---|---|---|---|---|---|
| **讀了幾份規格（/9）** | 4.6 [1–9] | **3.1** [0–5] | 7.1 [4–9] | 7.7 [4–9] | 8.3 [4–9] |
| 讀了 `Cart.items` | 27/100 | **1/100** | 63/100 | 71/100 | 86/100 |
| 讀了 `Cart.total` | 47/100 | 43/100 | 72/100 | 68/100 | 83/100 |
| 寫 / 跑測試次數 | 1.3 / 1.2 | 1.6 / 1.4 | 1.6 / 1.6 | 1.4 / 1.2 | 1.3 / 1.3 |
| 只改註解的重寫 | 0 | 0.0 | 0.1 | 0.0 | 0.0 |
| 步數 | 10.9 [4–18] | 10.3 [5–25] | 14.4 [9–25] | 15.9 [9–25] | 16.0 [12–25] |
| 不呼叫工具次數 | 0.8 | 0.7 | 0.9 | 1.4 | 0.9 |
| 重複呼叫次數 | 0 | 0.1 | 0.0 | 0.1 | 0.0 |
| Thought 平均字元數 | — | 24.8 | — | 27.3 | 25.1 |
| 內部思考總字元數 | 575 | 745 | 443 | 677 | 590 |
| 停止原因 | finish 100 | finish 98、loop 2 | finish 98、step_limit 2 | finish 99、step_limit 1 | finish 99、step_limit 1 |

**(c) 成本與可靠性**

| 指標 | act | react | act+fewshot | react+fewshot | +limit |
|---|---:|---:|---:|---:|---:|
| 輸入 token | 18,169 | 22,256 | 46,732 | 57,001 | 57,308 |
| 輸出 token | 2,087 | 2,265 | 2,680 | 2,733 | 2,615 |
| 耗時（秒） | 17.1 | 19.7 | 22.3 | 24.7 | 25.1 |
| 模型呼叫重試次數 | 0.1 | 0.3 | 0.1 | 0.4 | 0.5 |
| 重試後仍無法解析 | 0 | 0 | 0.0 | 0.0 | 0.0 |

**(d) 抓到的 bug 數分布**

| 條件 | 0 個 | 1 個 | 2 個 | 3 個 | 4 個 |
|---|---:|---:|---:|---:|---:|
| `act` | 20 | 9 | 48 | 21 | 2 |
| `react` | 25 | 10 | 60 | 5 | 0 |
| `act+fewshot` | 4 | 7 | 39 | 48 | 2 |
| `react+fewshot` | 8 | 5 | 21 | 60 | 6 |
| `react+fewshot+limit` | 7 | 3 | 31 | 58 | 1 |

### 10.5 統計檢定（事先決定的四個比較）

| 比較 | 指標 | A | B | 差（B − A） | p 值 |
|---|---|---:|---:|---:|---:|
| **Thought（無範例）**<br>act → react | 抓到的 bug | 1.8 | 1.4 | −0.31 | 0.035 |
| | invalid | 2.8 | 3.2 | +0.42 | 0.352 |
| | 讀了幾份規格 | 4.6 | 3.1 | −1.54 | **< 0.001** |
| | 輸入 token | 18,169 | 22,256 | +4,087 | 0.041 |
| **Thought（有範例）**<br>act+fewshot → react+fewshot | 抓到的 bug | 2.4 | 2.5 | +0.14 | 0.315 |
| | invalid | 1.4 | 1.3 | −0.12 | 0.601 |
| | 讀了幾份規格 | 7.1 | 7.7 | +0.54 | 0.062 |
| | 輸入 token | 46,732 | 57,001 | +10,269 | **< 0.001** |
| **範例**<br>無範例兩條件 → 有範例兩條件<br>（n = 200 對 200） | 抓到的 bug | 1.6 | 2.4 | +0.83 | **< 0.001** |
| | invalid | 3.0 | 1.3 | −1.66 | **< 0.001** |
| | 讀了幾份規格 | 3.9 | 7.4 | +3.51 | **< 0.001** |
| | 輸入 token | 20,212 | 51,866 | +31,654 | **< 0.001** |
| **告訴上限**<br>react+fewshot → +limit | 抓到的 bug | 2.5 | 2.4 | −0.08 | 0.597 |
| | invalid | 1.3 | 1.0 | −0.27 | 0.168 |
| | 讀了幾份規格 | 7.7 | 8.3 | +0.66 | 0.011 |
| | 輸入 token | 57,001 | 57,308 | +307 | 0.890 |

**多重比較**：共 16 個檢定。以 Bonferroni 校正（門檻 0.05 ÷ 16 ≈ 0.003）後：

| 結果 | p 值 | 校正後 |
|---|---:|---|
| 範例的四項效果 | < 0.001 | ✅ 顯著 |
| 無範例時，react 讀的規格較少 | < 0.001 | ✅ 顯著 |
| 有範例時，react 的 token 較多 | < 0.001 | ✅ 顯著 |
| 無範例時，react 抓到的 bug 較少 | 0.035 | 不顯著（傾向） |
| 無範例時，react 的 token 較多 | 0.041 | 不顯著（傾向） |
| 告訴上限使讀的規格變多 | 0.011 | 不顯著（傾向） |

**探索性分析**（非事先決定，僅供討論）
- 有範例時的 B3 抓到率：act+fewshot 53%、react+fewshot 67%（排列檢定 p = 0.062）。
- Thought 的效果方向隨範例改變：無範例時 −0.31、有範例時 +0.14，相差 0.45 個 bug（交互作用），未做檢定。
- 每條件 100 次中，含 echo 測試的執行次數：act 9、react 8、act+fewshot 9、react+fewshot 5、+limit 4。

### 10.6 案例分析（取自 n = 5 前導實驗）

**案例 A：只讀程式碼 → 教科書級的 assertion echo（react）**

動作順序：`read_spec` 2 次後，連續 `read_source` 9 次才開始寫測試。測試註解洩漏了期望值的來源：

```python
cart.add_item("gadget", 15, quantity=50)  # 750 base, discount 5% (since <100 and >50 triggers 5%)
```

規格是 `quantity >= 50 -> 10`，程式（B1）是 `> 50`；註解中的「>50」證明期望值來自程式碼。結果 echo B1，而且 0/4。
→ 實證了步驟 2 推導的機制；**有 Thought 也沒有阻止它跳過規格**。

**案例 B：憑直覺猜規則，剛好猜成 bug 的行為（react）**

```python
self.cart.add_item("toy", 500, quantity=2)  # subtotal 1000
# free shipping
total = self.cart.total(member=True, coupon="SAVE20")
assert total == 800.0
```

依規格：1000 → 打 8 折 800 → 800 < 1000 要付運費，會員半價 30 → 應為 830。它用優惠「前」的 1000 判斷免運，正是 B4 的行為。這次它**沒有讀程式碼**，卻仍然產生 echo。
→ **當 bug 實作的是常見的錯誤直覺時，憑直覺猜也會得到同樣的錯誤答案**（F11 的預測成真）。

**案例 C：同一份測試自相矛盾（act+fewshot）**

`"saVE15"` 被列在「無效優惠碼」中（echo B2），但同一份測試裡的另一個測試，正確地期望小寫有效（抓到 B2）。
→ agent 不會檢查測試之間的一致性。

**案例 D：為了讓測試通過，一步步摧毀自己的測試（act）**

| 步驟 | 動作 | 結果 |
|---:|---|---|
| 12 | 寫測試（13 個函式） | 4 failed、18 passed |
| 14 | 改寫 | 2 failed |
| 16 | 改寫 | 1 failed |
| 18、20 | 改寫 | 1 failed |
| 22 | 改寫成只剩 1 個函式 | 1 failed |

最終 0/4。第一版的失敗很可能正是真正的 bug，但 agent 把「失敗」當成要消除的問題。
→ **測試的目的變成「讓測試通過」，而不是「找 bug」**，比 echo 更極端。（可將各版本分別評分來確認，尚未執行。）

### 10.7 結論

1. **範例的影響遠大於 Thought**（p < 0.001）：抓到的 bug +0.83、誤報 −55%、讀的規格加倍；代價是輸入 token 約 2.6 倍。模型模仿的是範例的**動作**（讀完所有規格），而不是推理（呼應 F7）。
2. **Thought 本身沒有幫助；沒有範例時，反而使 agent 讀得更少**（4.6 → 3.1 份規格，p < 0.001；`Cart.items` 只在 1/100 次被讀到），抓到的 bug 也有變少的傾向。這與論文第 3.3 節的觀察一致：小型模型以 prompting 執行 ReAct 時表現最差，因為很難從少量範例同時學會推理與行動。
3. **Thought 總是增加成本**（有範例時輸入 token +22%，p < 0.001），而且 Thought 平均只有約 25 個字元，多半是動作標籤（F1）。
4. **論文「ReAct 優於 Act」的主張，在本設定（小型推理模型、原生工具呼叫、測試生成）下未被重現。**
5. **F10 假設被推翻，而且方向相反**：告訴步數上限後，讀的規格反而增加（7.7 → 8.3，p = 0.011，校正後不顯著）。
6. **assertion echo 很少見**（每次執行平均約 0.1 個）；主要問題是**誤報**與**沒讀規格就猜介面**。system prompt 中「期望值必須來自規格」的規則，可能是 echo 很少的原因（未驗證）。
7. **多跳 bug（B4）幾乎抓不到**（2–7%），這是所有條件共同的限制。
8. **單次執行的可靠性很低**：每個條件都同時出現過 0/4 與 3/4 以上。

---

## 11. Threats to validity

| 面向 | 說明 |
|---|---|
| 外部效度 | 只有一個被測程式（cart，約 160 行）、一個模型（gpt-oss:20b）、一種推理強度（low） |
| 指標解析度 | 只有 4 個 bug，難度分布不均：B1、B2 太簡單（約 70–90%）、B4 太難（2–7%），實際上主要靠 B3 區分條件 |
| 規格瑕疵 | `Cart` 類別說明洩漏了內部儲存格式（`name -> (unit_price, quantity)`），可能誘發 `items()` 的錯誤猜測 |
| prompt 設計 | Thought 的說明只有一句；範例只有一條，而且以文字形式放在 system prompt，而不是真正的工具呼叫歷史 |
| 推理模型 | gpt-oss 的內部思考無法完全關閉，所以 Act 並非「完全沒有推理」 |
| 規則的影響 | 「期望值必須來自規格」的規則在所有條件都存在，會壓低 echo 的絕對數量 |
| 統計 | 16 個檢定未事先校正；探索性分析並非事先決定 |
| 溫度 | 使用 Ollama 預設值，沒有明確設定 |

---

## 12. 工程上遇到的問題

| 問題 | 原因 | 解法 |
|---|---|---|
| `pip` 指令不存在 | 啟用的 `.venv` 已被刪除，實際使用的是系統 Python | 在專案資料夾重建 `.venv` |
| 找不到 `cart.py` | 資料夾改名後，路徑設定沒有同步 | 以 `Path(__file__)` 推算路徑，改指向 `subject/` |
| 模型回應空白、HTTP 500 | gpt-oss 內建工具呼叫格式，與文字協定衝突 | 改用 Ollama 原生 `tools` 參數 |
| `tool()` 函式參數名衝突 | 工具參數也叫 `name` | 改名為 `tool_name` |
| `step1_call_llm.py` 語法錯誤 | 加註解時多打一個字元，所有 import 它的檔案都無法執行 | 用 `python3 -m py_compile` 檢查 |
| Observation 夾雜 coverage 警告 | 上層 pytest 設定檔含 `--cov` | pytest 加上 `-o addopts=` |
| 背景執行一啟動就結束 | 伺服器上的 `step6_agent.py` 仍是舊版；25 次全部失敗卻只花 0 秒 | 覆蓋新版；正式執行前先用最小設定在前景試跑 |
| log 看不到進度 | Python 輸出導向檔案時會緩衝 | `python3 -u` |
| 同時執行兩批的風險 | 所有 agent 共用 `workspace/test_cart.py` | 一次只跑一批；改用 tmux 管理 |
| 36% 的執行因格式錯誤中斷 | 長段程式碼放進 JSON 參數時跳脫出錯 | 重試 3 次 + 告知模型格式錯誤；之後 0 次中斷 |
| 長時間實驗可能中斷 | 斷線、伺服器重開 | `--runs` 改為「每條件總共 N 次」，重跑同一個指令即可接續 |

---

## 13. 待辦與後續

- [ ] 案例 D：將各版本測試分別評分，確認是否刪除了會揭露 bug 的測試
- [ ] 探索性：以 mutation score 作為更細緻的指標（需標明為事後分析）
- [ ] 撰寫報告：Introduction、Implementation、Reflections、AI 使用聲明