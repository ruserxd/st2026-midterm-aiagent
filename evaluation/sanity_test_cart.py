"""量尺自我檢查用：每個測試的正確分類是「已知的」，用來確認評分程式判斷正確。

    test_revealing_b1     依規格寫        -> bug-revealing（抓到 B1）
    test_echo_b1          照抄 bug 的輸出  -> assertion-echo（B1）
    test_echo_b2          照抄 bug 的行為  -> assertion-echo（B2）
    test_echo_b3          照抄 bug 的輸出  -> assertion-echo（B3）
    test_echo_b4          照抄 bug 的輸出  -> assertion-echo（B4）
    test_invalid          規格與程式都不符 -> invalid（誤報）
    test_passing          正確但沒抓到 bug -> passing
"""

import pytest

import cart


def test_revealing_b1():
    assert cart.bulk_discount_percent(50) == 10


def test_echo_b1():
    assert cart.bulk_discount_percent(50) == 5


def test_echo_b2():
    with pytest.raises(ValueError):
        cart.parse_coupon("save10")


def test_echo_b3():
    c = cart.Cart()
    c.add_item("pen", 10, 1)
    c.remove_item("pen", 1)
    assert c.items() == {"pen": 0}


def test_echo_b4():
    c = cart.Cart()
    c.add_item("tv", 1100, 1)
    assert c.total(coupon="SAVE20") == 880.0


def test_invalid():
    assert cart.apply_discount(200, 15) == 171


def test_passing():
    assert cart.shipping_fee(0) == 60


def test_echo_combined_b1_b4():
    # 50 件 x 22 元，SAVE10：正確 951；只有 B1 1000.5；只有 B4 951；B1+B4 同時存在 940.5
    # 期望值 940.5 只在「多個 bug 同時存在」時成立 -> assertion-echo（combined）
    c = cart.Cart()
    c.add_item("pen", 22, 50)
    assert c.total(coupon="SAVE10") == 940.5