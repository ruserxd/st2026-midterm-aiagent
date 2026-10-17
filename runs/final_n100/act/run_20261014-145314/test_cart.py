import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- Tests for apply_discount ---

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0


def test_apply_discount_rounding():
    # 1% of 123 gives 1.23, so result should be 121.77
    assert apply_discount(123, 1) == pytest.approx(121.77)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-10, 20)


def test_apply_discount_invalid_percent():
    for bad in (-5, 105, 200):
        with pytest.raises(ValueError):
            apply_discount(100, bad)

# --- Tests for bulk_discount_percent ---

def test_bulk_discount_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15


def test_bulk_discount_invalid():
    for bad in (0, -1, 3.5):
        with pytest.raises(ValueError):
            bulk_discount_percent(bad)

# --- Tests for parse_coupon ---

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon(" SAVE50 ") == 50


def test_parse_coupon_invalid():
    for bad in ("", "SAVE0", "SAVEX", "DISCOUNT5", "SAVE51", "1234", "   "):
        with pytest.raises(ValueError):
            parse_coupon(bad)

# --- Tests for shipping_fee ---

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0


def test_shipping_fee_member():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=True) == 0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-5)

# --- Tests for Cart class ---

def test_cart_initially_empty():
    c = Cart()
    assert list(c.items()) == []
    assert c.subtotal() == 0
    assert c.total() == 60  # member False, no coupon


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 2.5, quantity=4)
    c.add_item("banana", 1.2)
    assert list(c.items()) == [("apple", (2.5, 4)), ("banana", (1.2, 1))]
    assert c.subtotal() == pytest.approx(2.5*4 + 1.2)

    # remove part of quantity
    c.remove_item("apple", 2)
    assert dict(c.items())["apple"][1] == 2

    # remove all quantity, item should be removed
    c.remove_item("banana")
    assert "banana" not in dict(c.items())


def test_cart_total_with_member_and_coupon():
    c = Cart()
    c.add_item("item", 500, quantity=2)  # subtotal 1000
    total = c.total(member=True, coupon="SAVE10")
    # subtotal 1000 -> shipping 0, discount 10% on total of items (1000)
    assert total == pytest.approx(1000 * 0.9)


def test_cart_total_bulk_discount():
    c = Cart()
    c.add_item("widget", 20, quantity=150)  # bulk discount 15%
    # subtotal before discount 3000
    # apply bulk discount: 15% -> 2550
    # shipping free (subtotal after discount >=1000)
    assert c.total() == pytest.approx(2550)


def test_cart_total_error_conditions():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -5)
    with pytest.raises(ValueError):
        c.remove_item("none")  # removing non-existent item should raise
