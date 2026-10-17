import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding_and_bounds():
    # percent at extremes
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0
    # rounding
    assert apply_discount(333, 10) == 299.7

    with pytest.raises(ValueError):
        apply_discount(-5, 10)
    with pytest.raises(ValueError):
        apply_discount(10, -1)
    with pytest.raises(ValueError):
        apply_discount(10, 101)

# ----- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_values():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

# ----- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe50") == 50

    with pytest.raises(ValueError):
        parse_coupon("SAV5")   # not enough digits for valid range? Actually 5 is in range, but missing digits? spec says integer N. This should be valid; skip.

# Testing boundary conditions
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")   # N must be >=1
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # >50
    with pytest.raises(ValueError):
        parse_coupon("SAVEE10")
    with pytest.raises(ValueError):
        parse_coupon(123)

# ----- shipping_fee -----------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

    # members pay half
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

    with pytest.raises(ValueError):
        shipping_fee(-10)

# ----- Cart class -------------------------------------------------------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60   # no items, subtotal 0 => shipping fee


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 50, quantity=3)
    assert c.items()["apple"] == (50, 3)
    assert c.subtotal() == 150
    # Adding more of same item increases quantity
    c.add_item("apple", 50, quantity=2)
    assert c.items()["apple"] == (50, 5)
    assert c.subtotal() == 250
    # Removing partially
    c.remove_item("apple", quantity=3)
    assert c.items()["apple"] == (50, 2)
    assert c.subtotal() == 100
    # Removing more than exists should remove the item completely
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()
    assert c.subtotal() == 0


def test_cart_total_with_discounts_and_shipping():
    c = Cart()
    # Add items to trigger bulk discount for a single item
    c.add_item("widget", 200, quantity=120)   # bulk percent should be 15%
    assert bulk_discount_percent(120) == 15
    subtotal_before = c.subtotal()  # 200 * 120 = 24000
    expected_after_bulk = apply_discount(subtotal_before, 15)
    assert round(c.total(member=False, coupon=None), 2) == expected_after_bulk + shipping_fee(expected_after_bulk)

    # Add a coupon that gives an additional discount after shipping
    c.add_item("gadget", 100, quantity=1)
    coupon_percent = parse_coupon("SAVE10")
    total_with_coupon = apply_discount(c.total(member=False, coupon=None), coupon_percent)
    assert round(total_with_coupon, 2) == round(
        (expected_after_bulk + shipping_fee(expected_after_bulk)) * (1 - coupon_percent/100), 2
    )

    # Member discount on shipping should reduce final total
    c.add_item("thing", 50, quantity=10)
    member_total = c.total(member=True, coupon="SAVE5")
    assert member_total < c.total(member=False, coupon="SAVE5")

# Edge case: adding negative or zero price/quantity should raise ValueError

def test_add_invalid():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -10)
    with pytest.raises(ValueError):
        c.add_item("zero", 0)
    with pytest.raises(ValueError):
        c.add_item("negqty", 5, quantity=-1)

# Edge case: removing non-existent item should raise KeyError

def test_remove_nonexistent():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("nothing")
