import pytest
from cart import Cart, parse_coupon, shipping_fee

# Helper

def make_cart(items):
    c = Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

def test_empty_cart_total_zero():
    c = Cart()
    assert c.total() == 0.00

# Test that total rounds to two decimals (even if shipping or discounts introduce many decimals)

def test_rounding_two_decimals():
    c = Cart()
    c.add_item("item", 1.005, 1)  # subtotal 1.005
    t = c.total()
    assert isinstance(t, float)
    assert round(t, 2) == t  # already rounded by implementation

# Test that invalid coupon raises ValueError

def test_invalid_coupon_error():
    c = Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALIDCODE")

# Test that a valid coupon reduces amount correctly and shipping added after discount

def test_valid_coupon_applies_and_shipping_added(monkeypatch):
    # mock parse_coupon to return 0.10 for any code
    monkeypatch.setattr("cart.parse_coupon", lambda code: 10)
    c = Cart()
    c.add_item("item", 100, 1)  # subtotal 100
    total_no_discount = c.total()
    total_with_coupon = c.total(coupon="ANYCODE")
    assert total_with_coupon < total_no_discount
    # shipping fee added after discount: ensure difference equals shipping_fee applied to discounted amount
    discounted_amount = 100 * (1 - 0.10)
    expected_shipping = shipping_fee(discounted_amount)
    assert round(total_with_coupon,2) == round(discounted_amount + expected_shipping,2)
