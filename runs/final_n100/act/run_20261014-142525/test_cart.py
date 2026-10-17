import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 99.99 * 20% = 79.992 -> rounded to 2 decimals
    assert apply_discount(99.99, 20) == round(99.99 * 0.8, 2)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)


def test_apply_discount_invalid_percent():
    for p in (-1, 101):
        with pytest.raises(ValueError):
            apply_discount(100, p)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_ranges():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15


def test_bulk_discount_percent_invalid():
    for q in (0, -3):
        with pytest.raises(ValueError):
            bulk_discount_percent(q)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon("  SaVe50  ") == 50


def test_parse_coupon_invalid_cases():
    for code in ("", "SAVEX", "SAVE0", "SAVE51", "OTHER20", "10SAVE"):
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(0) == 60
    # member discount
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(500, member=True) == 30


def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        shipping_fee(-1)

# ---------- Cart class ----------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}
    c.add_item("banana", 0.8, 3)
    assert c.items() == {"apple": 2, "banana": 3}
    # add more apples
    c.add_item("apple", 1.5, 1)
    assert c.items()["apple"] == 3
    # attempt to add with different price -> ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)
    # remove some bananas
    c.remove_item("banana", 2)
    assert c.items()["banana"] == 1
    # remove remaining banana
    c.remove_item("banana")
    assert "banana" not in c.items()
    # removing non-existent item -> KeyError
    with pytest.raises(KeyError):
        c.remove_item("orange")


def test_cart_subtotal_with_bulk_discount():
    c = Cart()
    # 10 units of item at $10 each => bulk discount 5%
    c.add_item("widget", 10, 10)
    assert bulk_discount_percent(10) == 5
    expected = round(10 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected


def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("thing", 200, 5)  # no bulk discount
    # subtotal = 1000
    assert c.subtotal() == 1000
    # apply coupon 10%
    total_after_coupon = apply_discount(1000, 10)
    # shipping fee on amount after coupon: 1000*0.9=900 < 1000 => 60
    expected_total = round(total_after_coupon + 60, 2)
    assert c.total(coupon="SAVE10") == expected_total


def test_cart_total_no_shipping_when_empty():
    c = Cart()
    assert c.total() == 0
