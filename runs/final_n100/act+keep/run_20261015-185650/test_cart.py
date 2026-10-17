import math
import cart
import pytest

# Helper for floating point comparison
EPS = 1e-9

def close(a, b):
    return abs(a - b) < EPS

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
@ pytest.mark.parametrize("percent", [0])
def test_apply_discount_invalid_price(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@ pytest.mark.parametrize("price", [100])
@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_ranges():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_standard():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    # Non-member
    assert cart.shipping_fee(50, member=False) == 60
    # Member pays half
    assert cart.shipping_fee(20, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    # Assuming typical coupon structure; spec didn't give examples.
    # We rely on implementation to accept strings starting with a number followed by '%'.
    assert isinstance(cart.parse_coupon('10%'), float)

@ pytest.mark.parametrize("code", ['abc', '200%', '-5%', '50'])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Cart functionality ----------

def test_cart_basic_operations():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    assert c.total() == 0

    c.add_item('apple', 10, quantity=2)
    assert c.items() == [('apple', 10, 2)]
    assert close(c.subtotal(), 20.0)
    # No coupon, non-member: shipping 60
    assert c.total(member=False) == 80.0
    # Member discount on subtotal (no coupon): shipping 30
    assert c.total(member=True) == 50.0

    # Add another item
    c.add_item('banana', 5)
    assert close(c.subtotal(), 25.0)
    assert c.items() == [('apple', 10, 2), ('banana', 5, 1)]

    # Remove some quantity
    c.remove_item('apple', quantity=1)
    assert c.items() == [('apple', 10, 1), ('banana', 5, 1)]
    assert close(c.subtotal(), 15.0)

    # Removing all should remove the item entirely
    c.remove_item('apple')
    assert c.items() == [('banana', 5, 1)]
    assert close(c.subtotal(), 5.0)

    # Test coupon application
    # Let's apply a valid 10% coupon on subtotal 5 => 4.5 + shipping (member True -> 30) => 34.5
    c = cart.Cart()
    c.add_item('orange', 5, quantity=1)
    assert close(c.total(member=True, coupon='10%'), 34.5)

# ---------- edge cases ----------

def test_cart_remove_nonexistent():
    c = cart.Cart()
    c.add_item('pear', 3, quantity=1)
    with pytest.raises(ValueError):
        c.remove_item('apple')

# ---------- integration bulk discount + coupon + shipping ----------

def test_bulk_discount_and_shipping():
    c = cart.Cart()
    # Add 120 units of 'widget' at $10 each
    c.add_item('widget', 10, quantity=120)
    # Subtotal: 1200 -> free shipping
    assert close(c.subtotal(), 1200.0)
    # Bulk discount percent should be 15%
    assert cart.bulk_discount_percent(120) == 15
    # Apply bulk discount via coupon? Not specified; assume manual apply
    discounted = cart.apply_discount(c.subtotal(), cart.bulk_discount_percent(120))
    assert close(discounted, 1020.0)
    # Total with member and no coupon should still be 1200 (free shipping)
    assert c.total(member=True) == 1200.0
