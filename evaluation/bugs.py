"""植入的 bug：以「文字替換」的方式定義在正確版 cart_fixed.py 上。

    正確版 cart_fixed.py  + 全部 4 個替換  = subject/cart.py（agent 實際測試的版本）
    正確版 cart_fixed.py  + 其中 1 個替換  = 單一 bug 版（用來判斷一個測試抓到的是哪個 bug）

注意：agent 的工具只會讀 subject/cart.py，看不到這個資料夾。
"""

from pathlib import Path

FIXED_PATH = Path(__file__).resolve().parent / "cart_fixed.py"

BUGS = {
    "B1": {
        "name": "bulk_boundary",
        "function": "bulk_discount_percent",
        "description": "邊界錯誤：剛好 50 件應打 10% 折扣，程式只給 5%（>= 寫成 >）",
        "old": "    if quantity >= 50:\n",
        "new": "    if quantity > 50:\n",
    },
    "B2": {
        "name": "coupon_case",
        "function": "parse_coupon",
        "description": "規格要求優惠碼不分大小寫，程式分大小寫（少了 .upper()）",
        "old": "    text = code.strip().upper()\n",
        "new": "    text = code.strip()\n",
    },
    "B3": {
        "name": "remove_zero",
        "function": "Cart.remove_item",
        "description": "移除最後一件後，商品以數量 0 留在購物車（<= 寫成 <）",
        "old": "        if line[1] <= 0:\n",
        "new": "        if line[1] < 0:\n",
    },
    "B4": {
        "name": "shipping_before_coupon",
        "function": "Cart.total",
        "description": "多跳：運費應以套用優惠碼『後』的金額計算，程式用套用前的金額",
        "old": "        return round(amount + shipping_fee(amount, member), 2)\n",
        "new": "        return round(amount + shipping_fee(self.subtotal(), member), 2)\n",
    },
}


def build_source(bug_ids=()):
    """回傳套用了指定 bug 的 cart 原始碼。"""
    src = FIXED_PATH.read_text(encoding="utf-8")
    for bug_id in bug_ids:
        old, new = BUGS[bug_id]["old"], BUGS[bug_id]["new"]
        if src.count(old) != 1:
            raise RuntimeError(f"{bug_id}: 找不到唯一的替換位置")
        src = src.replace(old, new)
    return src


def variants():
    """所有要拿來跑測試的版本：fixed、buggy、B1、B2、B3、B4。"""
    out = {"fixed": build_source(), "buggy": build_source(list(BUGS))}
    for bug_id in BUGS:
        out[bug_id] = build_source([bug_id])
    return out
