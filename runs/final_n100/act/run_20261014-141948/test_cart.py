import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Apply discount ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # round to 2 decimals
    assert apply_discount(333.3333, 10) == 299.99997  # not rounded? test rounding
    assert round(apply_discount(333.3333, 10), 2) == 300.0

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -1)
    with pytest.raises(ValueError):
        apply_discount(100, 101)

# ---------- Bulk discount percent --------------------------

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        bulk_discount_percent(3.2)  # non integer

# ---------- Parse coupon -----------------------------------

def test_parse_coupon_basic():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE20 ") == 20

def test_parse_coupon_errors():
    with pytest.raises(ValueError):
        parse_coupon("")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        parse_coupon("SAVEX10")
    with pytest.raises(ValueError):
        parse_coupon("123")

# ---------- Shipping fee ------------------------------------

def test_shipping_fee():
    assert shipping_fee(1200) == 0
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(0) == 60

def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-1)

# ---------- Cart class --------------------------------------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 2.0, quantity=3)
    assert c.items() == {"apple": 3}
    # add same item increases qty
    c.add_item("apple", 2.0, quantity=2)
    assert c.items() == {"apple": 5}
    # adding with different price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0)


def test_cart_remove_and_items():
    c = Cart()
    c.add_item("banana", 1.5, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items() == {"banana": 2}
    # removing more than existing removes item
    c.remove_item("banana", quantity=3)
    assert "banana" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("orange")


def test_cart_subtotal_and_bulk():
    c = Cart()
    # no items
    assert c.subtotal() == 0
    # single item quantity below bulk thresholds
    c.add_item("item", 10, quantity=9)
    assert c.subtotal() == 90.0
    # reach 10 units -> 5% discount
    c.remove_item("item", quantity=-1)  # actually can't negative; just add more
    c.add_item("item", 10, quantity=1)
    assert c.items()["item"] == 10
    expected = round(10 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected


def test_cart_total_no_coupon():
    c = Cart()
    c.add_item("item", 100, quantity=1)
    # subtotal 100, no discount, shipping 60 -> total 160
    assert c.total(member=False) == 160.0
    # member gets half shipping
    assert c.total(member=True) == 130.0


def test_cart_total_with_coupon():
    c = Cart()
    c.add_item("item", 200, quantity=1)
    # subtotal 200, apply coupon 10% -> 180, shipping 60 -> 240
    assert c.total(coupon="SAVE10") == 240.0
    # member gets half shipping: 210
    assert c.total(member=True, coupon="save10") == 210.0


def test_cart_total_errors():
    c = Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# ---------- Edge cases --------------------------------------

def test_cart_empty_shipping_zero():
    c = Cart()
    assert c.total() == 0
    assert c.subtotal() == 0
    # shipping should not be charged for empty cart
    assert shipping_fee(0) == 60  # but total handles empty case
