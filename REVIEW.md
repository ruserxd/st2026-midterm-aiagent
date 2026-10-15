# 審查報告：設計流程與程式碼檢查

> 審查日期：2026-10-15
> 範圍：`README.md` 的實驗設計，以及 `ai-agent/` 底下所有 `.py`
> 資料：`runs/final_n100/`（5 個條件 × 100 次）
> 狀態標記：✅ 已修正　⚠️ 未修正，需在報告中說明　ℹ️ 已驗證沒有問題

---

## 總覽

| # | 問題 | 類型 | 嚴重度 | 狀態 |
|---|---|---|---|---|
| 1 | 只在 bug 版無法載入時，每個測試都被算成 bug-revealing | 量尺 bug | 中 | ✅ 已修正 |
| 2 | echo 判斷沒有檢查 `buggy` 版（`combined`） | 量尺漏洞 | 低 | ✅ 已修正 |
| 3 | few-shot 範例含有抓 B1 的策略提示 | 設計混淆 | **高** | ⚠️ |
| 4 | 「讀的規格」沒有計入 `read_source` | 指標定義 | 中 | ⚠️ |
| 5 | README 內部矛盾 | 文件 | 低 | ⚠️ |
| 6 | 1 次執行超過上下文長度 | 效度 | 低 | ⚠️ |
| 7 | 重試失敗的呼叫沒有計入 token | 效度 | 低 | ⚠️ |
| 8 | collection error 混在「0 個 bug」中 | 呈現 | 低 | ⚠️ |
| 9 | 步驟 6 的設定是看過前導結果後才調整的 | 效度 | 低 | ⚠️ |
| 10 | `step2`、`step3` 的小問題 | 程式 | 低 | ⚠️ 刻意不改 |

**結論**：主要結論（範例的效果遠大於 Thought；Thought 本身沒有幫助）**不受量尺修正影響**，「抓到的 bug」最多只差 0.03。需要處理的是問題 3：它影響「範例效果」的解讀。

---

## 一、已修正的錯誤

### 1. 只在 bug 版無法載入時，每個測試都被算成 bug-revealing ✅

**位置**：`ai-agent/step7_evaluate.py` 的 `classify()`

**原因**：初版用 `outcomes[b].get(test) != "passed"` 判斷失敗。有些 agent 的測試檔會在模組層級呼叫 cart，例如在 import 時就執行 `parse_coupon("save10")`。這段程式在 fixed 版正常，在 B2 版會丟出例外，導致整份檔案在 B2 版無法載入，所有測試在 B2 版的結果都是 `missing`。由於 `missing != "passed"`，在 fixed 上通過的每個測試都被判為「抓到 B2」，包括根本沒測優惠碼的測試。

**實例**（`runs/final_n100/react+fewshot/run_20261014-152714/eval_tests.csv`）：

```text
test_add_item_increase_quantity, bug-revealing, B2, fixed=passed, B2=missing, ...
```

**影響**：n = 100 中有 8 次執行受影響。下表右欄是重算的估計值（只算真正 `failed` 的測試，不含檔案層級那一列），正式數字以重新評分後為準。

| 條件 | revealing 測試（修正前） | 修正後估計 | 抓到的 bug（修正前） | 若不計檔案層級 |
|---|---|---|---:|---:|
| act | 2.20 [max 5] | 2.20 [max 5] | 1.76 | 1.76 |
| react | 1.73 [max 16] | 1.59 [max 4] | 1.45 | 1.43 |
| act+fewshot | 3.79 [max 30] | 3.09 [max 7] | 2.37 | 2.34 |
| react+fewshot | 3.69 [max 31] | 3.05 [max 5] | 2.51 | 2.48 |
| react+fewshot+limit | 3.14 [max 22] | 2.93 [max 5] | 2.43 | 2.42 |

- **revealing 測試數被高估**：有範例的條件高估約 0.6 個，README §10.4 的最大值 30、31 就是這樣來的。
- **抓到的 bug 數不變**：修正後仍以檔案層級記為抓到 bug，所以與修正前相同。若改成不計檔案層級，最多只差 0.03，不影響任何檢定結論。

**修正**：
- 只有結果是 `"failed"` 的測試才算失敗，`missing` 不算。
- 只在 bug 版無法載入時，改由 `<collection error>` 這一列以**檔案層級**記為抓到該 bug。
- 驗證：`--selftest` 8 項全部正確。受影響的那次執行，revealing 測試從約 31 個變成 3 個，抓到的 bug 仍是 3/4。

**定義上的選擇**：檔案層級的載入錯誤確實是 bug 造成的，所以算成抓到 bug。如果認為 agent 沒有寫出針對該 bug 的測試、不該算，就把 `<collection error>` 那一列改回 `collection-error`，bug 數會變成上表最右欄的數字。

### 2. echo 判斷沒有檢查 `buggy` 版（`combined`） ✅

**原因**：初版只用 B1～B4 單一 bug 版判斷 echo。如果一個測試照抄的是「多個 bug 同時存在」時的輸出，它只會在 `buggy` 版通過，因此會被誤判為 invalid。

**修正**：加入 `buggy` 版的判斷，標記為 `combined`，不計入「抓到的 bug（/4）」。並在 `evaluation/sanity_test_cart.py` 加入 `test_echo_combined_b1_b4` 驗證。

**影響**：重算 n = 100 的資料，這種情況是 **0 次**，數據不變。

---

## 二、設計流程的問題（未修正）

### 3. few-shot 範例含有抓 B1 的策略提示 ⚠️ 高

**位置**：`ai-agent/step5_fewshot_agent.py` 的 `EXEMPLAR_REACT`

範例的內容不只是示範格式，還直接包含了解題策略：

| 範例內容 | 對應到 cart 的哪個部分 |
|---|---|
| `classify(25)` 的 bug 是 `>=` 寫成 `>` | 與 **B1** 是同一種 bug |
| *"Off-by-one bugs hide at boundaries, so I will test the value on each side of every boundary"* | 直接教了怎麼抓 **B1** |
| *"read the specification of EVERY function"* | 直接指示要讀完所有規格 |
| *"I must not guess what latest() returns"* | 對應 F10 的 `items()` 幻覺 |

**影響**：
- 結論 1「範例的效果遠大於 Thought」中，有一部分可能是**策略指示**的效果，而不是 few-shot 模仿機制的效果。
- Act 版刪掉 Thought 行之後，這些策略文字也一起不見了（只剩動作）。所以「Thought（有範例）」那組比較的其實是「Thought 機制 + 額外的策略文字」。論文附錄 C 也是這樣設計的，但需要說明。

**建議**：
- 至少在 §11 Threats 和 §10.7 結論 1 加註。
- 如果有時間，補一個「策略寫成 system prompt 規則、但不給範例」的條件，就能拆開兩者。原本的 500 次可以沿用，只需跑新條件（n = 100 約 40 分鐘）。

### 4. 「讀的規格」沒有計入 `read_source` ⚠️ 中

**位置**：`ai-agent/step8_experiment.py` 的 `load_runs()`，`specs_read` 只計算 `read_spec`

`read_source` 回傳的內容也包含 docstring（`step2_tools.py` 的 `ast.get_source_segment`），所以讀程式碼時其實也看到了規格。

| 條件 | 只算 `read_spec` | 加上 `read_source` | `read_source` 次數 |
|---|---:|---:|---:|
| act | 4.64 | 4.70 | 0.35 |
| react | 3.10 | **3.71** | **1.00** |
| act+fewshot | 7.11 | 7.18 | 0.32 |
| react+fewshot | 7.65 | 7.90 | 0.41 |
| react+fewshot+limit | 8.31 | 8.74 | 0.60 |

**影響**：結論 2「Thought 使 agent 讀得更少」的差距從 1.54 份縮小到約 1.0 份，方向不變。

**這同時是一個發現**：react 讀程式碼的次數約為 act 的 3 倍，與 §10.6 案例 A（只讀程式碼導致 echo）一致。建議寫進結論 2，並在 `step8_experiment.py` 增加「看過規格（spec 或 source）」的指標。這只需要重新彙整（`--aggregate-only`），不用重跑。

### 5. README 內部矛盾 ⚠️ 低

| 位置 | 問題 |
|---|---|
| §11 統計列 | 寫「16 個檢定未事先校正」，但 §10.5 已經做了 Bonferroni 校正 |
| §13 待辦 | 還留著「填入 Ollama 版本」，但 §2 已經填了 `0.30.7` |
| §10.7 結論 2 | 引用論文 §3.3「小型模型 prompting 時 ReAct 表現最差」，請對照原文確認。論文比較的是 PaLM-8B/62B 的 prompting 與 finetuning，gpt-oss 本身是推理模型，套用時要說明差異 |
| §10.4 | 「bug-revealing 測試」那一列要等重新評分後更新（見錯誤 1） |
| 檔名 | `READE.md` 應為 `README.md`（GitHub 不會自動顯示前者） |

### 6. 1 次執行超過上下文長度 ⚠️ 低

`runs/final_n100/act+fewshot/run_20261014-141028` 有一步的 input token 剛好是 **16383**，等於 `num_ctx = 16384` 的上限。Ollama 超過上限時會默默截掉前面的內容。這次執行最後是 `step_limit`，抓到 3/4。

500 次中只有這 1 次，其他條件的單步最大值約 12k，影響很小，建議在 §11 Threats 註記。

### 7. 重試失敗的呼叫沒有計入 token ⚠️ 低

**位置**：`ai-agent/step6_agent.py` 的重試迴圈

呼叫失敗（例如 HTTP 500）時不會有 `prompt_eval_count`，所以這些呼叫的成本沒有被計入。react 類條件的平均重試次數較多（0.3–0.5，act 只有 0.1），所以 **Thought 的成本被低估了**。方向對結論 3「Thought 總是增加成本」有利，建議寫一句。

### 8. collection error 混在「0 個 bug」中 ⚠️ 低

整份測試檔在 fixed 上就無法載入的比例：

| act | react | act+fewshot | react+fewshot | +limit |
|---:|---:|---:|---:|---:|
| 2% | 2% | 6% | 8% | 2% |

這是 agent 的品質問題，算成 0 個 bug 是合理的，但 §10.4(d) 的「0 個」裡有一部分是這個原因，建議分開列出。

### 9. 步驟 6 的設定是看過前導結果後才調整的 ⚠️ 低

步數上限 25、不告訴上限等設定，是看過步驟 4、5 的 n = 1 結果後才決定的。這屬於合理的開發流程，§10.1 也說明了「四個比較在看到 n = 100 之前已決定」，但正式實驗的設定並非完全事前決定，建議在 §11 Threats 提一句。

---

## 三、程式的小問題（刻意不改）

| 位置 | 問題 | 為什麼不改 |
|---|---|---|
| `step2_tools.py` 的 `read_spec` / `read_source` | 找不到函式時的提示寫 `list_functions[]`，這是舊的文字協定寫法，原生 tool calling 下應為 `list_functions` | 這段文字是 agent 看到的 Observation，改了會讓程式和產生 500 次結果的版本不一致，無法重現 |
| `step3_act_agent.py` 的 `run_tests` | 沒有 README §6.4 說的 `-o addopts=`。目前上層沒有 pytest 設定檔，所以沒有影響 | 同上 |

**建議**：維持原樣，在 README §12 註記。如果一定要改，先用 git tag 標記實驗當時的版本（例如 `exp-n100`）。

---

## 四、已驗證沒有問題 ℹ️

| 項目 | 驗證方式 | 結果 |
|---|---|---|
| Thought 不影響環境 | `step4`/`step6` 在執行工具前就 `args.pop("thought")` | ✅ 正確 |
| Thought 會留在上下文 | `check_thought_in_context.py` 的暗號測試 | ✅ 正確 |
| input token 是完整 prompt | 檢查 500 次的軌跡，每一步的 `prompt_eval_count` 都遞增，沒有被快取扣掉 | ✅ 成本比較有效 |
| 排列檢定 | 固定 seed、雙尾、`(hits + 1) / (n + 1)` 校正 | ✅ 正確 |
| 多 bug 交互作用的 echo | 重算 n = 100，誤判為 invalid 的測試 | ✅ 0 個 |
| 只改註解的重寫偵測 | `same_tests` 以 AST 比對，忽略註解 | ✅ 正確 |
| 一次回傳多個工具呼叫 | 檢查 500 次的軌跡 | ✅ 0 次，不影響步數統計 |

---

## 五、後續待辦

- [ ] 延伸實驗（tmux `ext`）跑完後，先備份 `runs/`，再重新評分主實驗的 500 次（延伸實驗已用新版評分）
- [ ] `python3 step8_experiment.py --out final_n100 --aggregate-only` 重新彙整
- [ ] 用新數據更新 README §10.4 的「bug-revealing 測試」那一列
- [ ] 處理問題 3：在 Threats 和結論 1 加註，或補一個新條件
- [ ] 處理問題 4：增加「看過規格（spec 或 source）」的指標，並更新結論 2
- [ ] 修正問題 5 的 README 矛盾
- [ ] 在 §11 Threats 補上問題 6、7、9
- [ ] 注意：延伸實驗寫在 `runs/final_n100/`，彙整時會和主實驗出現在同一張表
