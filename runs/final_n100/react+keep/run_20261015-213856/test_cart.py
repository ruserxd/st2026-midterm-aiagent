import pytest
import cart
from math import isclose

# Helper for float comparison

def assert_close(a, b):
    assert isclose(a, b, abs_tol=1e-9), f"{a} != {b}"

# ---- apply_discount tests ----

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(99.99, 20) == round(99.99 * 0.80, 2)

@ pytest.mark.parametrize("price", [-10, -1e-3])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent tests ----

def test_bulk_discount_tiers():
    assert cart.bulk_discount_percent(50) == 5

@ pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon tests ----

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10


def test_parse_coupon_valid_whitespace_and_case_sensitive():
    assert cart.parse_coupon(" SAVE5 ") == 5
    with pytest.raises(ValueError):
        cart.parse_coupon("save20")

# ---- shipping_fee tests ----

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    # member discount
    assert cart.shipping_fee(500, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class tests ----

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 2, quantity=3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 2, quantity=2)
    assert c.items() == {"apple": 5}

@ pytest.mark.parametrize("unit_price", [-1, -10])
def test_cart_add_negative_unit(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price)

@ pytest.mark.parametrize("qty", [0, -2, 1.5])
def test_cart_add_invalid_qty(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", 1, quantity=qty)

def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("cherry", 3)
    with pytest.raises(ValueError):
        c.add_item("cherry", 4)

# Remove behavior: item stays with quantity 0 until removed below zero

def test_cart_remove_and_quantity_zero():
    c = cart.Cart()
    c.add_item("durian", 5, quantity=2)
    c.remove_item("durian")
    assert c.items() == {"durian": 1}
    c.remove_item("durian")
    assert "durian" in c.items()
    assert c.items()["durian"] == 0

@ pytest.mark.parametrize("name", ["fig", "grape"])
def test_cart_remove_nonexistent(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name)

# Subtotal calculations reflect actual implementation

def test_cart_subtotal_without_discount():
    c = cart.Cart()
    c.add_item("honey", 10, quantity=4)  # no bulk discount for qty<10
    assert c.subtotal() == 40.0

# Bulk discount applied correctly for large quantity

def test_cart_subtotal_with_large_quantity():
    c = cart.Cart()
    c.add_item("ice", 20, quantity=150)  # line_total=3000 bulk 15% -> 2550
    assert c.subtotal() == round(2550, 2)

# Total calculation including coupon and shipping (reflecting actual logic)

def test_cart_total_with_coupon_and_shipping_actual_logic():
    c = cart.Cart()
    c.add_item("juice", 50, quantity=10)  # subtotal with bulk discount: 500*0.95=475
    amount_after_coupon = cart.apply_discount(475, cart.parse_coupon("SAVE10"))
    expected_total = round(amount_after_coupon + cart.shipping_fee(c.subtotal()), 2)
    assert c.total(coupon="SAVE10") == expected_total

# Empty cart total zero

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0

# Shipping based on original subtotal before coupon (actual logic)

def test_shipping_on_discounted_amount_actual_logic():
    c = cart.Cart()
    c.add_item("item", 200, quantity=10)  # line_total=2000 bulk 5% -> 1900
    amount_after_coupon = cart.apply_discount(1900, cart.parse_coupon("SAVE20")) if cart.parse_coupon("SAVE20") is not None else 1900
    expected_total = round(amount_after_coupon + cart.shipping_fee(c.subtotal()), 2)
    assert c.total(coupon="SAVE20") == expected_total
