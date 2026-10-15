"""步驟 7：獨立評分。不相信 agent 怎麼說，只看它寫的測試實際上做了什麼。

做法：把同一份 test_cart.py 分別跑在 6 個版本的 cart 上
    fixed   正確版（規格的標準答案）
    buggy   含全部 4 個 bug（agent 實際測試的版本，等於 subject/cart.py）
    B1..B4  每個版本只含 1 個 bug（用來判斷一個測試抓到的是「哪個」bug）

每個測試的分類：
    bug-revealing   在 fixed 通過，在某個 bug 版（含 buggy）失敗 -> 抓到 bug
                    只在 bug 版無法載入的測試檔，以 <collection error> 一列記為抓到該 bug
    passing         在每個版本都通過                       -> 正確，但沒抓到任何 bug
    assertion-echo  在 fixed 失敗，卻在某個 bug 版（含 buggy）通過 -> 期望值照抄了 bug 的行為
    invalid         在 fixed 和所有 bug 版都失敗            -> 期望值既不符規格也不符程式（誤報）
    collection-error 測試檔本身無法載入（例如語法錯誤）

整份測試的指標：抓到幾個 bug（/4）、各分類的數量、在 fixed 上的 line / branch coverage。

執行：
    python3 step7_evaluate.py              評分 runs/ 底下所有執行
    python3 step7_evaluate.py --selftest   先檢查量尺本身是否正確
    python3 step7_evaluate.py --file 路徑   只評分一個測試檔，並列出每個測試的結果
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evaluation"
RUNS_DIR = ROOT / "runs"
SUBJECT = ROOT / "subject" / "cart.py"

sys.path.insert(0, str(EVAL_DIR))
import bugs  # noqa: E402

BUG_IDS = list(bugs.BUGS)                      # ["B1", "B2", "B3", "B4"]


# =====================================================================
# 1. 在某個版本的 cart 上跑測試，回傳每個測試的結果
# =====================================================================
def parse_junit(xml_path):
    """讀 pytest 產生的 JUnit XML 報告：{測試名稱: passed / failed / skipped}。"""
    if not xml_path.exists():
        return {}
    results = {}
    for tc in ET.parse(xml_path).getroot().iter("testcase"):
        if not tc.get("classname"):                 # 測試檔本身無法載入（例如語法錯誤）
            results["<collection error>"] = "error"
            continue
        name = f"{tc.get('classname')}::{tc.get('name')}"
        if tc.find("failure") is not None or tc.find("error") is not None:
            results[name] = "failed"
        elif tc.find("skipped") is not None:
            results[name] = "skipped"
        else:
            results[name] = "passed"
    return results


def run_suite(test_file, cart_source, with_coverage=False):
    """在暫存資料夾放入「這個版本的 cart.py」與測試檔，執行 pytest。"""
    with tempfile.TemporaryDirectory(prefix="eval_") as tmp:
        tmp = Path(tmp)
        (tmp / "cart.py").write_text(cart_source, encoding="utf-8")
        shutil.copy(test_file, tmp / "test_cart.py")

        cmd = [sys.executable]
        if with_coverage:
            cmd += ["-m", "coverage", "run", "--branch", "--source=cart"]
        cmd += ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
                "--junitxml=report.xml", "test_cart.py"]
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}   # 只用暫存資料夾裡的 cart
        try:
            subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {}, None
        results = parse_junit(tmp / "report.xml")

        coverage = None
        if with_coverage and (tmp / ".coverage").exists():
            subprocess.run([sys.executable, "-m", "coverage", "json", "-o", "cov.json"],
                           cwd=tmp, env=env, capture_output=True, timeout=60)
            if (tmp / "cov.json").exists():
                t = json.loads((tmp / "cov.json").read_text())["totals"]
                coverage = {
                    "line": round(100 * t["covered_lines"] / max(t["num_statements"], 1), 1),
                    "branch": round(100 * t["covered_branches"] / max(t["num_branches"], 1), 1),
                }
        return results, coverage


# =====================================================================
# 2. 依照各版本的結果，替每個測試分類
# =====================================================================
def classify(outcomes, test):
    if test == "<collection error>":
        if outcomes["fixed"].get(test) == "error":
            return "collection-error", []
        # 只在 bug 版無法載入（例如模組層級呼叫了有 bug 的函式）：以檔案層級記為抓到 bug，
        # 不把該版本上 missing 的每個測試都算成 bug-revealing
        broken = [b for b in BUG_IDS if outcomes[b].get(test) == "error"] or ["combined"]
        return "bug-revealing", broken
    on_fixed = outcomes["fixed"].get(test, "missing")
    if on_fixed == "skipped":
        return "skipped", []
    on_buggy = outcomes["buggy"].get(test, "missing")
    if on_fixed == "passed":
        reveals = [b for b in BUG_IDS if outcomes[b].get(test) == "failed"]   # missing 不算失敗
        if reveals:
            return "bug-revealing", reveals
        if on_buggy == "failed":                 # 只有多個 bug 同時存在時才失敗
            return "bug-revealing", ["combined"]
        return "passing", []
    echoes = [b for b in BUG_IDS if outcomes[b].get(test) == "passed"]
    if echoes:
        return "assertion-echo", echoes
    if on_buggy == "passed":                     # 期望值等於「多個 bug 同時存在」時的輸出
        return "assertion-echo", ["combined"]
    return "invalid", []


def evaluate(test_file):
    variants = bugs.variants()
    outcomes, coverage = {}, None
    for name, source in variants.items():
        outcomes[name], cov = run_suite(test_file, source, with_coverage=(name == "fixed"))
        if name == "fixed":
            coverage = cov

    tests = sorted(set().union(*[set(r) for r in outcomes.values()]))
    rows, found, echoed = [], set(), set()
    counts = {"bug-revealing": 0, "passing": 0, "assertion-echo": 0, "invalid": 0, "skipped": 0,
              "collection-error": 0}
    for test in tests:
        category, related = classify(outcomes, test)
        counts[category] += 1
        if category == "bug-revealing":
            found.update(b for b in related if b in BUG_IDS)   # "combined" 不算單一 bug
        if category == "assertion-echo":
            echoed.update(b for b in related if b in BUG_IDS)
        rows.append({"test": test, "category": category, "bugs": ",".join(related),
                     **{f"on_{v}": outcomes[v].get(test, "missing") for v in variants}})

    return {
        "test_file": str(test_file),
        "n_tests": len(tests),
        "bugs_found": sorted(found),
        "bugs_echoed": sorted(echoed),
        "counts": counts,
        "failed_on_buggy": sum(1 for r in rows if r["on_buggy"] != "passed"),
        "coverage": coverage,
        "tests": rows,
    }


# =====================================================================
# 3. 輸出
# =====================================================================
def save(result, out_dir):
    out_dir = Path(out_dir)
    tests = result["tests"]
    (out_dir / "eval.json").write_text(
        json.dumps({k: v for k, v in result.items() if k != "tests"}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    if tests:
        with (out_dir / "eval_tests.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(tests[0]))
            writer.writeheader()
            writer.writerows(tests)


HEADER = (f"{'run':34s} {'tests':>5s} {'bugs':>5s} {'found':12s} "
          f"{'reveal':>6s} {'echo':>5s} {'invalid':>7s} {'line%':>6s} {'branch%':>7s}")


def row(label, r):
    cov = r["coverage"] or {}
    c = r["counts"]
    return (f"{label:34s} {r['n_tests']:5d} {len(r['bugs_found']):3d}/4 "
            f"{','.join(r['bugs_found']) or '-':12s} {c['bug-revealing']:6d} "
            f"{c['assertion-echo']:5d} {c['invalid']:7d} "
            f"{cov.get('line', '-'):>6} {cov.get('branch', '-'):>7}")


def check_subject():
    """確認 subject/cart.py 和「正確版 + 全部 bug」一模一樣，否則評分會對不上。"""
    if SUBJECT.read_text(encoding="utf-8") != bugs.build_source(BUG_IDS):
        print("⚠️  警告：subject/cart.py 和 evaluation/ 產生的 buggy 版本不一致，"
              "評分結果可能不準。\n")


def selftest():
    print("量尺自我檢查\n")
    ok = True
    ref = evaluate(EVAL_DIR / "reference_test_cart.py")
    print("1. 人工依規格寫的參考測試：應該 4/4、0 echo、0 invalid")
    print("   " + HEADER + "\n   " + row("reference", ref))
    ok &= ref["bugs_found"] == BUG_IDS and ref["counts"]["assertion-echo"] == 0 \
        and ref["counts"]["invalid"] == 0

    san = evaluate(EVAL_DIR / "sanity_test_cart.py")
    print("\n2. 已知分類的測試：每一行的分類都應該和註明的一樣")
    expected = {"test_revealing_b1": ("bug-revealing", "B1"), "test_echo_b1": ("assertion-echo", "B1"),
                "test_echo_b2": ("assertion-echo", "B2"), "test_echo_b3": ("assertion-echo", "B3"),
                "test_echo_b4": ("assertion-echo", "B4"), "test_invalid": ("invalid", ""),
                "test_passing": ("passing", ""),
                "test_echo_combined_b1_b4": ("assertion-echo", "combined")}
    for t in san["tests"]:
        short = t["test"].split("::")[-1]
        good = expected.get(short) == (t["category"], t["bugs"])
        ok &= good
        print(f"   {'✅' if good else '❌'} {short:20s} -> {t['category']:15s} {t['bugs']}")
    print("\n結果：", "全部正確，量尺可以使用" if ok else "有錯誤，請先不要相信評分結果")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--file", help="只評分這一個測試檔")
    args = ap.parse_args()

    check_subject()
    if args.selftest:
        sys.exit(0 if selftest() else 1)

    if args.file:
        r = evaluate(Path(args.file).resolve())
        print(HEADER + "\n" + row(Path(args.file).name, r) + "\n")
        for t in r["tests"]:
            print(f"  {t['category']:15s} {t['bugs']:8s} {t['test']}")
        return

    files = sorted(RUNS_DIR.rglob("test_cart.py"))
    if not files:
        print(f"在 {RUNS_DIR} 底下找不到任何 test_cart.py")
        return
    print(HEADER)
    for f in files:
        r = evaluate(f)
        save(r, f.parent)
        print(row(str(f.parent.relative_to(RUNS_DIR)), r))
    print("\n每次執行的詳細結果：runs/<執行>/eval.json 與 eval_tests.csv")


if __name__ == "__main__":
    main()