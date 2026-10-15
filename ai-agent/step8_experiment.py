"""步驟 8：正式實驗。每個條件跑 N 次、自動評分、彙整成一張比較表。

    條件                     Thought   範例   告訴步數上限   用途
    act                       ✗        ✗      ✗          主比較：Thought 的效果
    react                     ✓        ✗      ✗          主比較
    act+fewshot               ✗        ✓      ✗          範例的效果
    react+fewshot             ✓        ✓      ✗          範例的效果
    react+fewshot+limit       ✓        ✓      ✓          F10：告訴上限是否讓它少讀規格

執行順序是「輪流」：act → react → act+fewshot → ... → 再從 act 開始。
這樣伺服器負載等時間因素會平均分散到每個條件，不會集中在某一個條件。

執行：
    python3 step8_experiment.py                      每個條件 5 次（約 10 分鐘）
    python3 step8_experiment.py --runs 100 --out final_n100
                                                     每個條件 100 次，存到 runs/final_n100/
                                                     中斷後用同一個指令重跑，會從中斷處接續
    python3 step8_experiment.py --conditions act react
    python3 step8_experiment.py --aggregate-only     不跑 agent，只重新彙整已有的結果

輸出（runs/<--out>/，預設 runs/final/）：
    <條件>/run_<時間>/       每次執行的軌跡、統計、測試檔、評分
    runs.csv                每次執行一列，方便用 Excel 畫圖
    summary.md              比較表：平均 [最小–最大]，以及統計檢定
"""

import argparse
import csv
import json
import random
import statistics
import time
from collections import Counter

import step6_agent
import step7_evaluate
from step3_act_agent import ROOT

FINAL_DIR = ROOT / "runs" / "final"

CONDITIONS = {                       # 名稱: (模式, 範例, 告訴步數上限, 保留內部思考, 推理強度)
    "act": ("act", False, False, False, "low"),
    "react": ("react", False, False, False, "low"),
    "act+fewshot": ("act", True, False, False, "low"),
    "react+fewshot": ("react", True, False, False, "low"),
    "react+fewshot+limit": ("react", True, True, False, "low"),
    # 延伸實驗 1：把 gpt-oss 的內部思考放回歷史（KEEP_THINKING = True）
    "act+keep": ("act", False, False, True, "low"),
    "react+keep": ("react", False, False, True, "low"),
    # 延伸實驗 2：在表現最好的兩個條件上，把推理強度從 low 提高到 high
    "act+fewshot+high": ("act", True, False, False, "high"),
    "react+fewshot+high": ("react", True, False, False, "high"),
}
# high 推理的單步思考可長達 1 萬多 token，16384 會被用滿而截斷（試跑時發生），所以 high 條件加大上下文。
# low 條件單步從未接近 16384，維持原設定。
HIGH_NUM_CTX = 32768
MAIN_CONDITIONS = ["act", "react", "act+fewshot", "react+fewshot", "react+fewshot+limit"]

# cart 中所有「有規格」的函式；用來計算規格閱讀率
SPEC_TARGETS = ["apply_discount", "bulk_discount_percent", "parse_coupon", "shipping_fee",
                "Cart.add_item", "Cart.remove_item", "Cart.items", "Cart.subtotal", "Cart.total"]


# =====================================================================
# 1. 執行：輪流跑每個條件，跑完立刻評分
#    --runs N 的意思是「每個條件總共要有 N 次」。資料夾裡已經有的會算進去，
#    所以中途中斷（斷線、伺服器重開）後，用同一個指令重跑就會從中斷處接續。
# =====================================================================
def count_done(name):
    return len(list((FINAL_DIR / name).glob("run_*/eval.json")))


def run_all(conditions, target):
    need = {c: max(0, target - count_done(c)) for c in conditions}
    total = sum(need.values())
    if total == 0:
        print(f"每個條件都已經有 {target} 次，不需要再跑")
        return
    print(f"目標每個條件 {target} 次；還需要執行 {total} 次（已存在的結果會保留）\n")
    done, t0 = 0, time.time()
    while any(need.values()):
        for name in conditions:
            if need[name] == 0:
                continue
            mode, fewshot, limit, keep, think = CONDITIONS[name]
            done += 1
            k = count_done(name) + 1
            print(f"[{done:3d}/{total}] {name:20s} 第 {k:3d} 次 ", end="", flush=True)
            try:
                run_dir, stats = step6_agent.run_agent(mode, fewshot, tell_limit=limit,
                                                       keep_thinking=keep, think=think,
                                                       num_ctx=HIGH_NUM_CTX if think == "high"
                                                       else step6_agent.NUM_CTX,
                                                       verbose=False, out_dir=FINAL_DIR)
                test_file = run_dir / "test_cart.py"
                if not test_file.exists():
                    test_file.write_text("# the agent wrote no test file\n", encoding="utf-8")
                result = step7_evaluate.evaluate(test_file)
                step7_evaluate.save(result, run_dir)
                c = result["counts"]
                print(f"bugs={len(result['bugs_found'])}/4 {','.join(result['bugs_found']) or '-':12s} "
                      f"invalid={c['invalid']:2d} echo={c['assertion-echo']} "
                      f"steps={stats['steps']:2d} stop={stats['stop_reason']:13s} "
                      f"retry={stats['llm_retries']} "
                      f"{stats['wall_seconds']:5.1f}s")
            except Exception as exc:                    # 一次失敗不要讓整批中斷
                print(f"失敗：{type(exc).__name__}: {exc}")
            need[name] -= 1
            elapsed = time.time() - t0
            left = (total - done) * elapsed / done
            if done % 10 == 0:
                print(f"      -- 已花 {elapsed / 60:.0f} 分鐘，預估還要 {left / 60:.0f} 分鐘 --")
    print(f"\n全部完成，共 {(time.time() - t0) / 60:.1f} 分鐘")


# =====================================================================
# 2. 彙整：讀出每次執行的 summary.json、eval.json、trajectory.json
# =====================================================================
def normalize(name):
    name = (name or "").strip()
    return name[5:] if name.startswith("cart.") else name


def load_runs():
    rows = []
    for summary_path in sorted(FINAL_DIR.glob("*/run_*/summary.json")):
        run_dir = summary_path.parent
        eval_path = run_dir / "eval.json"
        if not eval_path.exists():
            continue
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        e = json.loads(eval_path.read_text(encoding="utf-8"))
        traj = json.loads((run_dir / "trajectory.json").read_text(encoding="utf-8"))
        specs_read = {normalize(t["args"].get("name")) for t in traj
                      if t.get("action") == "read_spec" and isinstance(t.get("args"), dict)}
        n_thoughts = sum(1 for t in traj if t.get("thought"))
        cov = e.get("coverage") or {}
        row = {
            "condition": run_dir.parent.name, "run": run_dir.name,
            "bugs_found": len(e["bugs_found"]),
            **{b: int(b in e["bugs_found"]) for b in step7_evaluate.BUG_IDS},
            "tests": e["n_tests"],
            "revealing": e["counts"]["bug-revealing"],
            "echo": e["counts"]["assertion-echo"],
            "invalid": e["counts"]["invalid"],
            "line_cov": cov.get("line"), "branch_cov": cov.get("branch"),
            "specs_read": sum(1 for t in SPEC_TARGETS if t in specs_read),
            "read_items": int("Cart.items" in specs_read),
            "read_total": int("Cart.total" in specs_read),
            "write_tests": s["tool_calls"].get("write_tests", 0),
            "run_tests": s["tool_calls"].get("run_tests", 0),
            "noop_rewrites": s.get("noop_rewrites", 0),
            "steps": s["steps"], "stop_reason": s["stop_reason"],
            "no_tool_call": s["no_tool_call"], "repeated_calls": s["repeated_calls"],
            "llm_retries": s.get("llm_retries", 0), "parse_failures": s.get("parse_failures", 0),
            "context_full_steps": s.get("context_full_steps", 0),
            "thought_avg_chars": round(s["thought_chars"] / n_thoughts, 1) if n_thoughts else None,
            "thinking_chars": s["thinking_chars"],
            "input_tokens": s["input_tokens"], "output_tokens": s["output_tokens"],
            "wall_seconds": s["wall_seconds"],
        }
        rows.append(row)
    return rows


def fmt(x):
    if x is None:
        return "–"
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}"


def mean_range(values):
    values = [v for v in values if v is not None]
    if not values:
        return "–"
    m = statistics.mean(values)
    if min(values) == max(values):
        return fmt(m)
    return f"{fmt(m)} [{fmt(min(values))}–{fmt(max(values))}]"


SUMMARY_ROWS = [  # (欄位, 顯示名稱, 方式)
    ("bugs_found", "抓到的 bug（/4）", "mean"),
    ("B1", "  B1 邊界", "rate"), ("B2", "  B2 大小寫", "rate"),
    ("B3", "  B3 移除商品", "rate"), ("B4", "  B4 運費順序（多跳）", "rate"),
    ("tests", "測試數", "mean"),
    ("revealing", "bug-revealing 測試", "mean"),
    ("echo", "assertion-echo 測試", "mean"),
    ("invalid", "invalid 測試（誤報）", "mean"),
    ("line_cov", "line coverage %", "mean"),
    ("branch_cov", "branch coverage %", "mean"),
    ("specs_read", "讀了幾份規格（/9）", "mean"),
    ("read_items", "  讀了 Cart.items", "rate"),
    ("read_total", "  讀了 Cart.total", "rate"),
    ("write_tests", "寫測試次數", "mean"),
    ("run_tests", "跑測試次數", "mean"),
    ("noop_rewrites", "只改註解的重寫", "mean"),
    ("steps", "步數", "mean"),
    ("no_tool_call", "不呼叫工具次數", "mean"),
    ("repeated_calls", "重複呼叫次數", "mean"),
    ("llm_retries", "模型呼叫重試次數", "mean"),
    ("parse_failures", "重試後仍無法解析", "mean"),
    ("context_full_steps", "上下文用滿而截斷的步數", "mean"),
    ("thought_avg_chars", "Thought 平均字元數", "mean"),
    ("thinking_chars", "內部思考總字元數", "mean"),
    ("input_tokens", "輸入 token", "mean"),
    ("output_tokens", "輸出 token", "mean"),
    ("wall_seconds", "耗時（秒）", "mean"),
]


def aggregate():
    rows = load_runs()
    if not rows:
        print(f"{FINAL_DIR} 底下沒有已評分的執行")
        return
    with (FINAL_DIR / "runs.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    groups = {}
    for r in rows:
        groups.setdefault(r["condition"], []).append(r)
    order = [c for c in CONDITIONS if c in groups] + sorted(c for c in groups if c not in CONDITIONS)

    lines = ["| 指標 | " + " | ".join(f"{c} (n={len(groups[c])})" for c in order) + " |",
             "|---|" + "---|" * len(order)]
    for key, label, how in SUMMARY_ROWS:
        cells = []
        for c in order:
            vals = [r[key] for r in groups[c]]
            cells.append(f"{sum(vals)}/{len(vals)}" if how == "rate" else mean_range(vals))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    stop_cells = []
    for c in order:
        counts = Counter(r["stop_reason"] for r in groups[c])
        stop_cells.append(", ".join(f"{k} {v}" for k, v in counts.most_common()))
    lines.append("| 停止原因 | " + " | ".join(stop_cells) + " |")
    lines += ["", "格式：平均 [最小–最大]；「k/n」代表 n 次執行中有 k 次。"]
    lines += compare(groups)

    md = "\n".join(lines) + "\n"
    (FINAL_DIR / "summary.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"已輸出 {FINAL_DIR / 'summary.md'} 與 {FINAL_DIR / 'runs.csv'}")

# =====================================================================
# 3. 統計檢定：兩個條件的差異，有多大機率只是運氣？
#    排列檢定（permutation test）：把兩組的結果混在一起、隨機重新分組很多次，
#    看「隨機分組」產生的差異，有多常和實際觀察到的差異一樣大（或更大）。
#    這個比例就是 p 值；p 越小，越不像是運氣造成的。
# =====================================================================
COMPARISONS = [  # (名稱, A 組條件, B 組條件)
    ("Thought 的效果（沒有範例）", ["act"], ["react"]),
    ("Thought 的效果（有範例）", ["act+fewshot"], ["react+fewshot"]),
    ("範例的效果（兩種模式合併）", ["act", "react"], ["act+fewshot", "react+fewshot"]),
    ("告訴步數上限的效果（F10）", ["react+fewshot"], ["react+fewshot+limit"]),
    # 延伸實驗（在看到 keep 條件的結果之前決定）
    ("保留內部思考的效果", ["act"], ["act+keep"]),
    ("推理的形式：內部思考 vs thought 參數", ["react"], ["act+keep"]),
    ("在保留內部思考時，Thought 的效果", ["act+keep"], ["react+keep"]),
    # 延伸實驗 2（在看到 high 條件的結果之前決定）；主要看 B4 與成本
    ("推理強度 low → high（act+fewshot）", ["act+fewshot"], ["act+fewshot+high"], "high"),
    ("推理強度 low → high（react+fewshot）", ["react+fewshot"], ["react+fewshot+high"], "high"),
    ("在 high 推理下，Thought 的效果", ["act+fewshot+high"], ["react+fewshot+high"], "high"),
]
HIGH_METRICS = [("bugs_found", "抓到的 bug"), ("B4", "抓到 B4（0/1）"), ("invalid", "invalid 測試"),
                ("output_tokens", "輸出 token"), ("wall_seconds", "耗時（秒）")]
TESTED_METRICS = [("bugs_found", "抓到的 bug"), ("invalid", "invalid 測試"),
                  ("specs_read", "讀了幾份規格"), ("input_tokens", "輸入 token")]


def permutation_p(a, b, n_perm=10000, seed=0):
    rng = random.Random(seed)                     # 固定 seed：每次執行結果都相同，可以重現
    observed = abs(statistics.mean(b) - statistics.mean(a))
    pooled = a + b
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        diff = abs(statistics.mean(pooled[len(a):]) - statistics.mean(pooled[:len(a)]))
        hits += diff >= observed - 1e-12
    return (hits + 1) / (n_perm + 1)


def compare(groups):
    lines = ["", "## 統計檢定（排列檢定，雙尾，10,000 次）", "",
             "| 比較 | 指標 | A 平均 | B 平均 | 差（B − A） | p 值 |", "|---|---|---|---|---|---|"]
    for title, a_conds, b_conds, *kind in COMPARISONS:
        metrics = HIGH_METRICS if kind == ["high"] else TESTED_METRICS
        if not all(c in groups for c in a_conds + b_conds):
            continue
        for key, label in metrics:
            a = [r[key] for c in a_conds for r in groups[c] if r[key] is not None]
            b = [r[key] for c in b_conds for r in groups[c] if r[key] is not None]
            if len(a) < 2 or len(b) < 2:
                continue
            p = permutation_p(a, b)
            ma, mb = statistics.mean(a), statistics.mean(b)
            lines.append(f"| {title}（A={'+'.join(a_conds)}，n={len(a)}；B={'+'.join(b_conds)}，n={len(b)}）"
                         f" | {label} | {fmt(ma)} | {fmt(mb)} | {mb - ma:+.2f} | {p:.3f} |")
    lines += ["", "p < 0.05 常被當作「不太像運氣」的門檻；但同時比較很多項時，"
              "總會有一些剛好低於 0.05，解讀時要保守。"]
    return lines



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5, help="每個條件總共要有幾次（已存在的會算進去）")
    ap.add_argument("--out", default="final", help="結果存在 runs/<這個名稱>/")
    ap.add_argument("--conditions", nargs="+", default=MAIN_CONDITIONS, choices=list(CONDITIONS))
    ap.add_argument("--aggregate-only", action="store_true")
    a = ap.parse_args()
    FINAL_DIR = ROOT / "runs" / a.out
    if not a.aggregate_only:
        step7_evaluate.check_subject()
        run_all(a.conditions, a.runs)
    aggregate()