import pytest
import cart

# Helper for rounding expected results
from decimal import Decimal

def round2(x):
    return round(float(Decimal(str(x))), 2)

# --- apply_discount tests ---

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 110])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent tests ---

def test_bulk_discount_zero():
    assert cart.bulk_discount_percent(1) == 0

def test_bulk_discount_ten():
    assert cart.bulk_discount_percent(10) == 5

def test_bulk_discount_fifty():
    assert cart.bulk_discount_percent(50) == 10

def test_bulk_discount_hundred():
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --- parse_coupon tests ---

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "FOO10", "SAVEX", "SAVE -5", " SAVE10a "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---

def test_shipping_free_over():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.5) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Non-member fee

def test_shipping_non_member():
    assert cart.shipping_fee(800) == 60
    assert cart.shipping_fee(500.25) == 60

# Member fee half

def test_shipping_member_half():
    assert cart.shipping_fee(400, member=True) == 30
    assert cart.shipping_fee(0, member=True) == 30

# --- Cart class tests ---

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    assert c.total() == 0

@ pytest.mark.parametrize("name,price,qty", [
    ("apple", 1.5, 3),
    ("banana", 2.0, 2),
])
def test_cart_add_item(name, price, qty):
    c = cart.Cart()
    c.add_item(name, price, qty)
    assert len(c.items()) == 1
    assert c.subtotal() == round2(price * qty)


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("cherry", 5, 4)
    c.remove_item("cherry", 2)
    # Remaining quantity should be 2
    assert any(item['quantity'] == 2 for item in c.items())
    assert c.subtotal() == round2(5 * 2)
    # Removing more than existing -> remove all
    c.remove_item("cherry", 5)
    assert c.items() == []
    assert c.subtotal() == 0

# Cart total with coupon and shipping logic

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, 1)   # subtotal 200
    # Apply SAVE10 => 20 discount -> 180, then shipping 60 -> 240 total
    assert round2(c.total(coupon="SAVE10")) == 240.0

# Cart total respects member discount on shipping after coupon

def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item("gadget", 500, 1)   # subtotal 500
    # After coupon SAVE20 -> 400; shipping fee 60 but member gets half 30 => 430
    assert round2(c.total(member=True, coupon="SAVE20")) == 430.0

# Empty cart returns 0 total and no shipping

def test_cart_empty_total_no_shipping():
    c = cart.Cart()
    assert c.total() == 0

# Invalid coupon raises ValueError

def test_cart_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("thing", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
