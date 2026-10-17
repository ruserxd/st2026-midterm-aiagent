# Revert to original complete test file
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def filled_cart(empty_cart):
    empty_cart.add_item("apple", 1.00, quantity=3)
    empty_cart.add_item("banana", 0.50, quantity=6)
    return empty_cart

# apply_discount tests

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -5])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-10, 110])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk_discount_percent tests

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(25) == 5
    assert bulk_discount_percent(51) == 10
    assert bulk_discount_percent(75) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

# parse_coupon tests

def test_parse_coupon_valid():
    code = "SAVE20"
    percent = parse_coupon(code)
    assert percent == 20

@ pytest.mark.parametrize("code", ["invalid", "SAVE", "SAVExxx", 123])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests

def test_shipping_fee_non_member():
    assert shipping_fee(50, member=False) == 60.0
    assert shipping_fee(1200, member=False) == 0.0

def test_shipping_fee_member():
    assert shipping_fee(50, member=True) == 30.0
    assert shipping_fee(1200, member=True) == 0.0

# Cart class tests

def test_cart_initial_state(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0

def test_add_and_remove_item(filled_cart):
    cart = filled_cart
    assert cart.subtotal() == 6.0
    cart.remove_item("apple", quantity=1)
    assert cart.items()["apple"] == 2
    # After removing one apple, subtotal should be $5.00 (no bulk discount)
    assert cart.subtotal() == 5.0
    cart.remove_item("banana")
    assert cart.items()["banana"] == 5

@ pytest.mark.parametrize(
    "name,price,qty", [
        ("orange", -1, 2),
        ("melon", 3, 0),
        ("lemon", 1.5, -3),
    ],
)
def test_add_item_invalid_arguments(empty_cart, name, price, qty):
    with pytest.raises(ValueError):
        empty_cart.add_item(name, price, quantity=qty)

# total calculation tests

def test_total_basic(filled_cart):
    cart = filled_cart
    subtotal = cart.subtotal()
    bulk_pct = bulk_discount_percent(9)
    amount_after_coupon = apply_discount(subtotal, bulk_pct)
    shipping = shipping_fee(amount_after_coupon, member=False)
    expected_total = round(amount_after_coupon + shipping, 2)
    assert cart.total() == expected_total

def test_total_with_coupons_and_member(filled_cart):
    cart = filled_cart
    amount = cart.subtotal()
    amount_after_coupon = apply_discount(amount, parse_coupon("SAVE20"))
    shipping = shipping_fee(cart.subtotal(), member=True)
    expected_total = round(amount_after_coupon + shipping, 2)
    assert cart.total(member=True, coupon="SAVE20") == expected_total
