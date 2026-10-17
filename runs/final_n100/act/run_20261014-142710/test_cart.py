import pytest
from math import isclose
import cart

# Helper: use spec for apply_discount

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    # No rounding needed for simple case
    assert cart.apply_discount(100, 25) == 75.0

@ pytest.mark.parametrize("price,percent,expected", [
    (0, 0, 0.0),
    (10.5, 0, 10.5),
    (50, 100, 0.0),
])
def test_apply_discount_edge(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent spec (assumed from context)
def test_bulk_discount_percent():
    # Assuming discount increases linearly: e.g., 5% for 5 items
    assert cart.bulk_discount_percent(1) == 0.0
    assert cart.bulk_discount_percent(10) == 10.0

# parse_coupon spec (example from repo?)
def test_parse_coupon_valid_and_invalid():
    # For a valid code, returns a tuple (name, discount)
    assert cart.parse_coupon("SAVE20") == ("SAVE20", 20)
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")

# shipping_fee spec: member flag changes rate

def test_shipping_fee():
    assert cart.shipping_fee(50) == 5.0   # example for non-member
    assert cart.shipping_fee(100, member=True) == 0.0

# Cart class tests

def test_cart_initially_empty():
    c = cart.Cart()
    assert list(c.items()) == []
    assert c.subtotal() == 0.0
    assert c.total() == 5.0   # shipping for empty? depends spec; assume base shipping


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, quantity=3)
    c.add_item("banana", 0.5)
    assert set(c.items()) == {"apple", "banana"}
    assert c.subtotal() == 3*1.0 + 0.5

    # Remove some apples
    c.remove_item("apple", quantity=2)
    assert c.subtotal() == 1.0*1 + 0.5
    # Remove last banana
    c.remove_item("banana")
    assert list(c.items()) == ["apple"]


def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item("item", 100, quantity=2)  # subtotal 200
    # No discount or shipping for members
    assert c.total(member=True) == 200.0
    # With coupon: assume SAVE20 gives 20% off before shipping
    assert c.total(coupon="SAVE20") == 170.0 + cart.shipping_fee(170)

# Test that Cart.total respects bulk discounts if applicable

def test_cart_total_bulk_discount():
    c = cart.Cart()
    # Add 10 units of same item, unit price 10 => subtotal 100
    c.add_item("bulk", 10, quantity=10)
    discount_percent = cart.bulk_discount_percent(10)
    expected_subtotal = 100 * (1 - discount_percent/100.0)
    assert c.total() == pytest.approx(expected_subtotal + cart.shipping_fee(expected_subtotal))

# Parameterize coupon application via Cart.total
@ pytest.mark.parametrize("coupon_code,expected", [
    ("SAVE20", 170.0),   # from earlier example
])
def test_cart_total_coupon(coupon_code, expected):
    c = cart.Cart()
    c.add_item("product", 200)
    assert c.total(coupon=coupon_code) == pytest.approx(expected + cart.shipping_fee(expected))
