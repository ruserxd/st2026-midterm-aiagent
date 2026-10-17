import pytest
from cart import Cart, bulk_discount_percent, shipping_fee, parse_coupon, apply_discount

# Helper function for floating point comparison
TOL = 1e-9

def assert_close(a,b):
    assert abs(a-b) < TOL, f"{a} != {b}"

# ----- Tests for bulk_discount_percent -----

def test_bulk_discount_no_items():
    # No discount before quantity 5
    assert bulk_discount_percent(0) == 0.0
    assert bulk_discount_percent(3) == 0.0
    assert bulk_discount_percent(4) == 0.0


def test_bulk_discounts():
    # 5-9 items => 10% discount
    assert bulk_discount_percent(5) == 10
    assert bulk_discount_percent(7) == 10
    # 10+ items => 20% discount
    assert bulk_discount_percent(10) == 20
    assert bulk_discount_percent(15) == 20

# ----- Tests for apply_discount -----

def test_apply_discount_exact():
    assert apply_discount(100, 10) == 90.0
    assert apply_discount(50, 25) == 37.5


def test_apply_discount_rounding():
    # Ensure rounding to two decimals
    assert apply_discount(99.999, 20) == 79.9992
    assert round(apply_discount(99.999, 20), 4) == 79.9992

# ----- Tests for shipping_fee -----

def test_shipping_fee_regular():
    # Below threshold: flat $5.00
    assert shipping_fee(50) == 5.0
    # Exactly at threshold: no fee
    assert shipping_fee(100) == 0.0
    # Above threshold: free
    assert shipping_fee(150) == 0.0

def test_shipping_fee_member():
    # Member gets free shipping regardless of subtotal
    assert shipping_fee(20, member=True) == 0.0
    assert shipping_fee(200, member=True) == 0.0

# ----- Tests for parse_coupon -----

def test_parse_valid_coupons():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('20OFF') == 20
    assert parse_coupon('50pct') == 50

def test_parse_invalid_coupons():
    with pytest.raises(ValueError):
        parse_coupon('abc')
    with pytest.raises(ValueError):
        parse_coupon('')
    with pytest.raises(ValueError):
        parse_coupon('999')

# ----- Tests for Cart class -----

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == []
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = Cart()
    c.add_item('apple', 1.00, quantity=3)
    c.add_item('banana', 0.50, quantity=2)
    assert c.items() == ['apple', 'banana']
    # Subtotal without discount
    expected_sub = round(3*1.00 + 2*0.5, 2)
    assert c.subtotal() == expected_sub
    # Remove one apple
    c.remove_item('apple')
    assert c.items() == ['banana']
    # Subtotal after removal
    assert c.subtotal() == round(2*0.5, 2)
    # Removing non-existent item should raise KeyError
    with pytest.raises(KeyError):
        c.remove_item('cherry')


def test_subtotal_with_bulk_discount():
    c = Cart()
    # Add 7 items of a product costing $10 each -> 10% bulk discount
    c.add_item('widget', 10.00, quantity=7)
    # Base total 70, discount 10% => 63.0
    assert c.subtotal() == 63.0


def test_total_no_coupon_or_member():
    c = Cart()
    c.add_item('item', 20.0, quantity=4)  # subtotal 80 (no discount)
    # shipping fee since subtotal <100
    expected_shipping = 5.0
    total_expected = round(80 + expected_shipping, 2)
    assert c.total() == total_expected


def test_total_with_coupon_and_member():
    c = Cart()
    c.add_item('item', 60.0, quantity=2)  # subtotal 120 (no bulk discount)
    # Coupon SAVE10 gives 10% off -> 108.0
    # Shipping fee after coupon: still <100? 108 >100 so free shipping
    total_expected = round(108.0 + 0.0, 2)
    assert c.total(member=True, coupon='SAVE10') == total_expected


def test_total_invalid_coupon_raises():
    c = Cart()
    c.add_item('item', 20.0)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')

# Ensure that rounding is applied correctly in total calculation

def test_total_rounding_behavior():
    c = Cart()
    # Use a price that leads to fractional cents
    c.add_item('precise', 0.3333, quantity=3)  # 0.9999 -> rounded to 1.00 subtotal
    assert c.subtotal() == 1.0
    # No coupon, shipping fee since subtotal <100
    total = c.total()
    assert_close(total, 6.0)  # 1.00 + 5.00 shipping => 6.00
