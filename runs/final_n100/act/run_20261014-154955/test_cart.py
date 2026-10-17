import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent

# Helper for creating a cart with items

def make_cart(items):
    c = Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

# Test subtotal calculation

def test_subtotal_single_and_multiple_items():
    cart_obj = make_cart([
        ("apple", 1.00, 3),   # 3.00
        ("banana", 0.50, 4)   # 2.00
    ])
    assert cart_obj.subtotal() == pytest.approx(5.00)

# Test total without discount or shipping for empty cart

def test_total_empty_cart():
    c = Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon="SAVE10") == 0

# Test coupon parsing and application

def test_coupon_parsing_and_application():
    # Valid coupon
    percent = parse_coupon("SAVE20")
    assert percent == 20
    cart_obj = make_cart([("item", 50, 1)])
    # 20% off: 40 + shipping on 40
    expected_total = round(40 + shipping_fee(40), 2)
    assert cart_obj.total(coupon="SAVE20") == expected_total

# Test invalid coupon raises ValueError

def test_invalid_coupon_raises():
    with pytest.raises(ValueError):
        Cart().total(coupon="INVALID")

# Test shipping fee logic

def test_shipping_fee_rules():
    # No shipping if subtotal <= 0
    assert shipping_fee(0) == 0
    # Free for members
    assert shipping_fee(5, member=True) == 0
    # Subtotal between 10 and 25 => flat $5
    assert shipping_fee(15) == 5
    # Subtotal over 25 => 4% of subtotal
    assert shipping_fee(30) == pytest.approx(1.2)

# Test bulk discount percentage calculation

def test_bulk_discount_percent():
    # 0% for qty <= 10
    assert bulk_discount_percent(5) == 0
    # 5% for qty between 11 and 20
    assert bulk_discount_percent(15) == 5
    # 10% for qty > 20
    assert bulk_discount_percent(25) == 10

# Test total rounding to two decimals

def test_total_rounding():
    c = Cart()
    c.add_item("precise", 0.3333, 3)  # subtotal 0.9999
    assert c.total() == round(0.9999, 2)
