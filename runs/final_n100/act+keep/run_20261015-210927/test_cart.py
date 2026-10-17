import pytest
import cart

# Helper to create a Cart with some items

def make_cart(items):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# 1. subtotal calculation (includes bulk discount)

def test_subtotal():
    c = make_cart([
        ("apple", 0.50, 4),   # $2.00, no bulk discount
        ("banana", 0.30, 10), # $3.00 with 5% bulk discount -> $2.85
    ])
    assert c.subtotal() == pytest.approx(4.85)

# 2. empty cart subtotal is zero

def test_empty_cart_subtotal():
    c = cart.Cart()
    assert c.subtotal() == 0

# 3. total without coupon or member shipping should add standard fee

def test_total_without_coupon_or_member():
    c = make_cart([
        ("item", 10, 1),
    ])
    expected_shipping = cart.shipping_fee(10)
    assert c.total() == pytest.approx(round(10 + expected_shipping, 2))

# 4. total with a valid coupon reduces amount before shipping

def test_total_with_coupon():
    c = make_cart([
        ("item", 20, 1),
    ])
    coupon_percent = cart.parse_coupon("SAVE25")
    amount_after_coupon = 20 * (1 - coupon_percent / 100)
    expected_shipping = cart.shipping_fee(amount_after_coupon)
    expected_total = round(amount_after_coupon + expected_shipping, 2)
    assert c.total(coupon="SAVE25") == pytest.approx(expected_total)

# 5. invalid coupon raises ValueError

def test_invalid_coupon_raises():
    c = make_cart([("item", 5, 1)])
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# 6. empty cart total is zero (no shipping)

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0

# 7. member flag affects shipping_fee calculation

def test_member_shipping_fee_difference():
    subtotal = 50
    non_member_fee = cart.shipping_fee(subtotal, member=False)
    member_fee = cart.shipping_fee(subtotal, member=True)
    assert member_fee <= non_member_fee
    assert member_fee > 0 or subtotal == 0
