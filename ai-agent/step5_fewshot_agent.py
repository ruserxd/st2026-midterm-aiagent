"""步驟 5：few-shot 範例。在 system prompt 加上一條「示範軌跡」，看 Thought 的品質會不會提升。

對應論文附錄 C：ReAct 的 prompt 不只有規則，還有幾條人工寫好的完整軌跡，
模型是「看範例模仿」才學會好的 Thought。步驟 4 我們只給了一句說明，Thought 很淺。

做法（和論文相同的消融方式）：
  - 範例用另一個模組 thermo（不是 cart），避免直接洩漏答案
  - ReAct 拿到完整範例：Thought + Action + Observation
  - Act  拿到同一條範例，但所有 Thought 行都刪掉（strip_thoughts）
  - 範例中的 Observation 是真的執行工具得到的輸出，不是編的
其他一切沿用步驟 4（同一個 run_agent），只替換 system prompt。

範例刻意示範的推理類型（論文第 2 節列出的 Thought 種類）：
  - 擬定計畫              Step 1 的 Plan
  - 追蹤進度              "Unread specs: ..."、"Still unread: ..."
  - 避免猜測              "I must not guess what latest() returns."
  - 從觀察中擷取重點        讀完規格後整理出邊界與已知值
  - 處理例外、判斷誰錯了    測試失敗時，分辨「測試寫錯」與「程式違反規格」

執行：
    python3 step5_fewshot_agent.py react
    python3 step5_fewshot_agent.py act
結果存在 runs/fewshot/<模式>_<時間>/
"""

import sys

import step4_react_agent as base

EXEMPLAR_REACT = """Task: Module under test: `thermo`. Write test_thermo.py.
Thought: Plan: list the functions, read the specification of EVERY function before testing it, take expected values only from the specifications, run the tests, then decide for each failure whether the test or the module is wrong.
Action: list_functions()
Observation: def c_to_f(celsius)
def classify(celsius)
class Log:
    def __init__(self)
    def add(self, celsius)
    def latest(self)
Thought: There are 2 functions and a class Log with add and latest. Unread specs: c_to_f, classify, Log.add, Log.latest. Start with c_to_f.
Action: read_spec(name="c_to_f")
Observation: Convert Celsius to Fahrenheit: F = C * 9 / 5 + 32, rounded to 1 decimal.
Thought: c_to_f: F = C * 9 / 5 + 32, rounded to 1 decimal. Known points: 0 -> 32.0, 100 -> 212.0, -40 -> -40.0. Next: classify.
Action: read_spec(name="classify")
Observation: Classify a temperature given in Celsius.

    celsius < 0          -> "freezing"
    0 <= celsius < 15    -> "cold"
    15 <= celsius < 25   -> "mild"
    celsius >= 25        -> "hot"

Raise ValueError if celsius is below absolute zero (-273.15).
Thought: classify has boundaries at 0, 15 and 25, and rejects values below -273.15. Off-by-one bugs hide at boundaries, so I will test the value on each side of every boundary, one input per test case. Still unread: Log.add and Log.latest. I must not guess what latest() returns.
Action: read_spec(name="Log.latest")
Observation: Return the most recent reading as a tuple (index, celsius),
where index counts readings from 0. Raise IndexError if the log is empty.
Thought: latest() returns a tuple (index, celsius) with index counting from 0, and raises IndexError on an empty log. Still unread: Log.add.
Action: read_spec(name="Log.add")
Observation: Append a reading (in Celsius) to the log.
Thought: add only appends a reading. I have now read every specification, so I can write the tests.
Action: write_tests(code=
```python
import pytest
import thermo


@pytest.mark.parametrize("c, f", [(0, 32.0), (100, 212.0), (-40, -40.0), (36.6, 97.88)])
def test_c_to_f(c, f):
    assert thermo.c_to_f(c) == f


@pytest.mark.parametrize("c, label", [
    (-0.1, "freezing"), (0, "cold"), (14.9, "cold"),
    (15, "mild"), (24.9, "mild"), (25, "hot"),
])
def test_classify_boundaries(c, label):
    assert thermo.classify(c) == label


def test_classify_absolute_zero_is_valid():
    assert thermo.classify(-273.15) == "freezing"


def test_classify_below_absolute_zero():
    with pytest.raises(ValueError):
        thermo.classify(-273.16)


def test_latest_returns_index_and_value():
    log = thermo.Log()
    log.add(20.5)
    log.add(21.0)
    assert log.latest() == (1, 21.0)


def test_latest_on_empty_log_raises():
    with pytest.raises(IndexError):
        thermo.Log().latest()
```
)
Observation: Wrote test_thermo.py: 36 lines, 6 test functions.
Thought: Run the tests.
Action: run_tests()
Observation: ...F.....F....                                                           [100%]
=================================== FAILURES ===================================
___________________________ test_c_to_f[36.6-97.88] ____________________________
test_thermo.py:7: in test_c_to_f
    assert thermo.c_to_f(c) == f
E   assert 97.9 == 97.88
E    +  where 97.9 = <function c_to_f>(36.6)
E    +    where <function c_to_f> = thermo.c_to_f
_______________________ test_classify_boundaries[25-hot] _______________________
test_thermo.py:15: in test_classify_boundaries
    assert thermo.classify(c) == label
E   AssertionError: assert 'mild' == 'hot'
E     
E     - hot
E     + mild
=========================== short test summary info ============================
FAILED test_thermo.py::test_c_to_f[36.6-97.88] - assert 97.9 == 97.88
FAILED test_thermo.py::test_classify_boundaries[25-hot] - AssertionError: ass...
2 failed, 12 passed in 0.02s
Thought: Two failures. (1) c_to_f(36.6): 36.6 * 9 / 5 + 32 = 97.88, but the spec says round to 1 decimal, so the correct value is 97.9. MY expected value was wrong, so I fix the test. (2) classify(25) returned 'mild', but the spec says celsius >= 25 is 'hot'. That expected value comes from the spec, so the MODULE is wrong; I keep this test unchanged.
Action: write_tests(code=
```python
import pytest
import thermo


@pytest.mark.parametrize("c, f", [(0, 32.0), (100, 212.0), (-40, -40.0), (36.6, 97.9)])
def test_c_to_f(c, f):
    assert thermo.c_to_f(c) == f


@pytest.mark.parametrize("c, label", [
    (-0.1, "freezing"), (0, "cold"), (14.9, "cold"),
    (15, "mild"), (24.9, "mild"), (25, "hot"),
])
def test_classify_boundaries(c, label):
    assert thermo.classify(c) == label


def test_classify_absolute_zero_is_valid():
    assert thermo.classify(-273.15) == "freezing"


def test_classify_below_absolute_zero():
    with pytest.raises(ValueError):
        thermo.classify(-273.16)


def test_latest_returns_index_and_value():
    log = thermo.Log()
    log.add(20.5)
    log.add(21.0)
    assert log.latest() == (1, 21.0)


def test_latest_on_empty_log_raises():
    with pytest.raises(IndexError):
        thermo.Log().latest()
```
)
Observation: Wrote test_thermo.py: 36 lines, 6 test functions.
Thought: Run again to confirm that only the real spec violation still fails.
Action: run_tests()
Observation: .........F....                                                           [100%]
=================================== FAILURES ===================================
_______________________ test_classify_boundaries[25-hot] _______________________
test_thermo.py:15: in test_classify_boundaries
    assert thermo.classify(c) == label
E   AssertionError: assert 'mild' == 'hot'
E     
E     - hot
E     + mild
=========================== short test summary info ============================
FAILED test_thermo.py::test_classify_boundaries[25-hot] - AssertionError: ass...
1 failed, 13 passed in 0.02s
Thought: Only classify(25) fails, and it is a real spec violation. Every function has been tested, so I finish.
Action: finish(summary="classify(25) returns 'mild', but the specification says temperatures >= 25 are 'hot'.")
Observation: Episode finished."""


def strip_thoughts(text):
    """刪除所有 Thought 行：Act 版本的範例（論文 Act baseline 的做法）。"""
    return "\n".join(line for line in text.splitlines() if not line.startswith("Thought: "))


EXEMPLAR_ACT = strip_thoughts(EXEMPLAR_REACT)

INTRO = {
    "react": ("\n\nBelow is an example episode on a different module (`thermo`). It is written "
              "as text, but you must make real tool calls. Each \"Thought:\" line in the example "
              "is what goes into the `thought` argument of that tool call.\n\n"),
    "act": ("\n\nBelow is an example episode on a different module (`thermo`). It is written "
            "as text, but you must make real tool calls.\n\n"),
}

original_system_prompt_for = base.system_prompt_for     # 步驟 4 的 prompt：規則（+ ReAct 的一句話）


def system_prompt_with_example(mode):
    example = EXEMPLAR_REACT if mode == "react" else EXEMPLAR_ACT
    return original_system_prompt_for(mode) + INTRO[mode] + example


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "react"

    # 把步驟 4 的兩個設定換掉，其餘完全沿用：
    base.system_prompt_for = system_prompt_with_example  # 1. system prompt 加上範例
    base.RUNS_DIR = base.ROOT / "runs" / "fewshot"       # 2. 結果存到另一個資料夾

    # 把實際送出的 system prompt 存起來，方便檢查兩種模式到底差在哪
    base.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (base.RUNS_DIR / f"system_prompt_{mode}.txt").write_text(
        system_prompt_with_example(mode), encoding="utf-8")

    base.run_agent(mode)