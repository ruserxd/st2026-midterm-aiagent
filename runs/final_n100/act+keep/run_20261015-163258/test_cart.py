import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper Functions for Tests ----------

# Create a simple cart with known items
@pytest.fixture
def sample_cart():
    cart = Cart()
    # item: name, unit_price, quantity
    cart.add_item("apple", 100.0, 5)   # subtotal 500, bulk discount 5% -> 475.0
    cart.add_item("banana", 50.0, 12)  # subtotal 600, bulk discount 5% -> 570.0
    return cart

# ---------- Tests for apply_discount ----------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent ----------

def test_bulk_discount_bounds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25 ") == 25
    assert parse_coupon(" SAVE5") == 5

@ pytest.mark.parametrize("code", ["SAVEE1", "save0", "sAvE51", "foo"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Tests for shipping_fee ----------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1200) == 0
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(500) == 60

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart operations ----------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("widget", 10.0, 3)
    assert cart.items() == {"widget": 3}
    # Add same item again increases quantity but unit price must match
    cart.add_item("widget", 10.0, 2)
    assert cart.items() == {"widget": 5}
    with pytest.raises(ValueError):
        cart.add_item("widget", 12.0, 1)  # price mismatch

@ pytest.mark.parametrize("unit_price,quantity", [(-1, 1), (10, 0), (10, -2)])
def test_cart_add_invalid(unit_price, quantity):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("error", unit_price, quantity)

# Removal tests

def test_cart_remove_and_zero_removal_bug():
    cart = Cart()
    cart.add_item("gadget", 20.0, 1)
    # Removing the exact quantity should delete the item entirely.
    # Implementation incorrectly keeps an entry with quantity 0.
    cart.remove_item("gadget", 1)
    assert "gadget" not in cart.items()

    # Remove more than existing -\u003e key deleted and no KeyError
    cart.add_item("widget", 5.0, 2)
    cart.remove_item("widget", 3)  # quantity goes below zero
    assert "widget" not in cart.items()

    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")

# ---------- Tests for subtotal calculation ----------

def test_cart_subtotal_with_bulk_and_rounding():
    cart = Cart()
    # 10 units of price 100 -\u003e bulk discount 5% (0.05)
    cart.add_item("alpha", 100, 10)  # line total 1000, discount 50 -> 950
    # 50 units of price 20 -\u003e bulk discount 10%
    cart.add_item("beta", 20, 50)   # line total 1000, discount 100 -> 900
    expected = round(950 + 900, 2)
    assert cart.subtotal() == expected

# ---------- Tests for total calculation and shipping bug ----------

def test_cart_total_coupon_and_shipping_bug():
    cart = Cart()
    # Create subtotal > 1000 but after 20% coupon < 1000 to trigger shipping fee.
    cart.add_item("expensive", 200, 6)   # 1200 total, no bulk discount
    # Subtotal is 1200.
    # Apply coupon of 20% -> 960 (<1000)
    total = cart.total(member=False, coupon="SAVE20")
    # Expected: amount after coupon 960 + shipping fee 60 = 1020.00
    assert total == 1020.00

# Empty cart total

def test_cart_total_empty():
    empty = Cart()
    assert empty.total() == 0
