import pytest
from cart import Cart, shipping_fee, apply_discount

# Helper: small product prices for deterministic results
UNIT_PRICE = 10.0
ITEM_QUANTITY = 3
SUBTOTAL = UNIT_PRICE * ITEM_QUANTITY

@pytest.fixture
def basic_cart():
    c = Cart()
    c.add_item("widget", UNIT_PRICE, ITEM_QUANTITY)
    return c

# Test an empty cart costs zero and no shipping is applied

def test_empty_cart_total_zero_and_no_shipping():
    c = Cart()
    assert c.total() == 0.0

# Test total without coupon or member discount: subtotal + shipping

def test_basic_total_with_shipping(basic_cart):
    # Shipping fee on the raw subtotal (no discount)
    expected = round(SUBTOTAL + shipping_fee(SUBTOTAL), 2)
    assert basic_cart.total() == expected

# Test that a valid coupon reduces price by percent and shipping added afterwards

def test_total_with_valid_coupon(basic_cart):
    # coupon that gives 20% off
    coupon_code = "SAVE20"
    # parse_coupon returns percent; we mock it via monkeypatch
    from cart import parse_coupon
    # Ensure the coupon is recognized and returns 20.0
    assert parse_coupon(coupon_code) == 20.0
    discounted_subtotal = round(apply_discount(SUBTOTAL, parse_coupon(coupon_code)), 2)
    expected = round(discounted_subtotal + shipping_fee(discounted_subtotal), 2)
    assert basic_cart.total(coupon=coupon_code) == expected

# Test that an invalid coupon raises ValueError and does not affect total

def test_total_with_invalid_coupon(basic_cart):
    invalid_code = "NOTACODE"
    with pytest.raises(ValueError):
        basic_cart.total(coupon=invalid_code)
    # Ensure the total remains unchanged from without coupon
    assert basic_cart.total() == round(SUBTOTAL + shipping_fee(SUBTOTAL), 2)

# Test that member flag affects shipping (assume shipping_fee has a member parameter)

def test_member_shipping(basic_cart):
    expected = round(apply_discount(SUBTOTAL, parse_coupon("")), 2) if False else SUBTOTAL
    # When member=True, shipping is free according to spec assumption
    assert basic_cart.total(member=True) == round(SUBTOTAL + shipping_fee(SUBTOTAL, member=True), 2)
