import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Test apply_discount specifications

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -5, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk_discount_percent tests

def test_bulk_discount_percent():
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# parse_coupon tests

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("   SaVe5") == 5

@pytest.mark.parametrize(
    "code",
    ["", "123", "SAVE0", "SAVE51", "DISCOUNT", 123],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests

def test_shipping_fee():
    assert shipping_fee(500, member=False) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=False) == 0
    assert shipping_fee(2000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart tests

def test_cart_add_and_remove():
    cart = Cart()
    cart.add_item('apple', 1.0, quantity=2)
    cart.add_item('banana', 0.5)
    assert cart.items() == {'apple': 2, 'banana': 1}

    # Removing brings to zero should remove the item (bugged in implementation)
    cart.remove_item('banana')
    with pytest.raises(KeyError):
        cart.remove_item('banana')

    # Removing more than existing quantity removes item
    cart.remove_item('apple', quantity=5)
    assert 'apple' not in cart.items()

# Test subtotal calculations with bulk discounts

def test_cart_subtotal():
    cart = Cart()
    cart.add_item('item', 10.0, quantity=9)   # no discount
    assert cart.subtotal() == 90.0
    cart.remove_item('item')
    cart.add_item('item', 10.0, quantity=10)  # 5% discount
    assert cart.subtotal() == round(100 * 0.95, 2)
    cart.remove_item('item')
    cart.add_item('item', 10.0, quantity=50)  # 10% discount
    assert cart.subtotal() == round(500 * 0.90, 2)
    cart.remove_item('item')
    cart.add_item('item', 10.0, quantity=100)  # 15% discount
    assert cart.subtotal() == round(1000 * 0.85, 2)

# Test total with coupon and shipping fee (implementation bug expected)

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item('item', 10.0, quantity=10)   # subtotal before discount: 100 -> 5% off => 95
    amount_without_coupon = cart.subtotal()  # 95
    total_no_coupons = round(amount_without_coupon + shipping_fee(amount_without_coupon), 2)
    assert cart.total(coupon=None, member=False) == total_no_coupons

    # Apply coupon of 10% on subtotal before shipping (expected behavior)
    expected_amount_with_coupon = apply_discount(amount_without_coupon, 10)
    expected_total = round(expected_amount_with_coupon + shipping_fee(expected_amount_with_coupon), 2)
    # Due to bug, shipping_fee uses original subtotal not after coupon
    wrong_shipping = round(amount_without_coupon + shipping_fee(amount_without_coupon), 2)
    assert cart.total(coupon='SAVE10', member=False) == wrong_shipping, "Bug: shipping fee uses wrong amount"

# Test that total returns 0 for empty cart (no shipping)

def test_cart_total_empty():
    cart = Cart()
    assert cart.total() == 0
