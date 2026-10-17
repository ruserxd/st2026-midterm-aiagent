import pytest
from cart import Cart, bulk_discount_percent, shipping_fee, apply_discount, parse_coupon

# Helper to create a cart with items

def build_cart(items):
    c = Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# 1. Test that subtotal sums correctly and applies bulk discount when quantity>10

def test_subtotal_basic_and_bulk_discount():
    cart = build_cart([
        ('apple', 1.00, 5),   # no bulk
        ('banana', 2.00, 12)  # bulk: discount percent from bulk_discount_percent(12)
    ])
    expected_subtotal = (1.00 * 5) + (apply_discount(2.00, bulk_discount_percent(12)) * 12)
    assert cart.subtotal() == pytest.approx(expected_subtotal)

# 2. Test shipping fee applied correctly on subtotal after coupon and member flag

def test_shipping_fee_and_coupon():
    cart = build_cart([
        ('widget', 20.00, 1)
    ])
    # No coupon: subtotal 20, shipping 60 (member False) => total 80
    assert cart.total() == pytest.approx(80.0)
    # Coupon gives 10% discount: subtotal after coupon 18, shipping 60 => total 78
    assert cart.total(coupon='SAVE10') == pytest.approx(78.0)

# 3. Test that invalid coupon raises ValueError

def test_invalid_coupon_raises():
    cart = build_cart([
        ('thing', 5.00, 1)
    ])
    with pytest.raises(ValueError):
        cart.total(coupon='invalid')

# 4. Test member flag discounts shipping fee by half

def test_member_discount_shipping_fee():
    cart = build_cart([
        ('thing', 100.00, 1)
    ])
    # Non-member: shipping 60 - total 160
    assert cart.total() == pytest.approx(160.0)
    # Member: shipping 30, total 130
    assert cart.total(member=True) == pytest.approx(130.0)

# 5. Test empty cart returns zero and no shipping

def test_empty_cart_total_zero():
    c = Cart()
    assert c.total() == 0
    assert c.subtotal() == 0
