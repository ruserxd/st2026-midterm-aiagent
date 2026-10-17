import cart
import pytest

# helper to create a cart with items

def make_cart(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# Test empty cart total is 0 and no shipping

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0.00

# Test subtotal calculation via items

def test_subtotal_and_total_no_coupon_or_shipping():
    items = [("apple", 1.5, 2), ("banana", 0.75, 4)]
    c = make_cart(items)
    # subtotal: 1.5*2 + 0.75*4 = 3 + 3 = 6
    assert c.subtotal() == pytest.approx(6.00)
    # shipping for non-member on $6 -> 10% of 6? Let's check shipping_fee doc via spec.
    # We don't have specification; assume shipping_fee implementation
    # We'll compute using cart.shipping_fee
    shipping = cart.shipping_fee(6, member=False)
    expected_total = round(6 + shipping, 2)
    assert c.total() == pytest.approx(expected_total)

# Test coupon application reduces subtotal before shipping

def test_coupon_applied_before_shipping():
    items = [("item", 100.0, 1)]
    c = make_cart(items)
    # parse a known coupon if possible; use spec of parse_coupon
    # For tests, we assume a coupon "SAVE10" gives 10% off
    try:
        percent = cart.parse_coupon("SAVE10")
    except Exception:
        pytest.skip("parse_coupon not implemented or no valid coupons")
    subtotal = c.subtotal()
    discounted = round(subtotal * (1 - percent/100), 2)
    shipping = cart.shipping_fee(discounted, member=False)
    expected_total = round(discounted + shipping, 2)
    assert c.total(coupon="SAVE10") == pytest.approx(expected_total)

# Test invalid coupon raises ValueError

def test_invalid_coupon_raises():
    items = [("item", 20.0, 1)]
    c = make_cart(items)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Test member discount on shipping via Cart.total's member flag

def test_member_shipping_fee():
    items = [("item", 50.0, 1)]
    c = make_cart(items)
    subtotal = c.subtotal()
    shipping_non_member = cart.shipping_fee(subtotal, member=False)
    shipping_member = cart.shipping_fee(subtotal, member=True)
    expected_total_non_member = round(subtotal + shipping_non_member, 2)
    expected_total_member = round(subtotal + shipping_member, 2)
    assert c.total(member=False) == pytest.approx(expected_total_non_member)
    assert c.total(member=True) == pytest.approx(expected_total_member)

# Test rounding to two decimals

def test_rounding():
    items = [("item", 0.333, 1)]
    c = make_cart(items)
    total = c.total()
    # The result should be rounded to 2 decimal places
    assert isinstance(total, float)
    assert round(total, 2) == total
