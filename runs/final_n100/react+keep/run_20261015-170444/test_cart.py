import pytest
from cart import (
    parse_coupon,
    apply_discount,
    bulk_discount_percent,
    shipping_fee,
    Cart,
)

# ---------- Coupon parsing tests ----------

def test_parse_valid_coupons():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon("  Save20 ") == 20

@ pytest.mark.parametrize("code", ["SAVEX", "discount10", "save0", "SAVE51", ""])

def test_parse_invalid_coupons(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])

def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -5, 105, 101])

def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_bands():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty", [0, -1, 2.5])

def test_bulk_discount_invalid_quantity(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- shipping_fee tests ----------

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0

@ pytest.mark.parametrize("subtotal,expected", [(500,30),(800,30),(1200,0)])
def test_shipping_fee_member(subtotal, expected):
    assert shipping_fee(subtotal, member=True) == expected

# ---------- Cart functionality tests ----------

def test_add_and_items():
    cart = Cart()
    cart.add_item("apple", 2.0)
    cart.add_item("banana", 1.5, quantity=3)
    assert cart.items() == {"apple":1, "banana":3}

@ pytest.mark.parametrize("unit_price", [-1, -10])
def test_add_negative_unit_price(unit_price):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("apple", unit_price)

@ pytest.mark.parametrize("qty", [0, -2, 3.5])
def test_add_invalid_quantity(qty):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("apple", 1.0, quantity=qty)

# Updating existing item with same unit price

def test_update_existing_same_price():
    cart = Cart()
    cart.add_item("socks", 5.0, quantity=2)
    cart.add_item("socks", 5.0, quantity=3)
    assert cart.items() == {"socks":5}

# Adding same item with different price should error

def test_update_existing_different_price():
    cart = Cart()
    cart.add_item("tshirt", 20.0)
    with pytest.raises(ValueError):
        cart.add_item("tshirt", 25.0)

# Remove item tests

def test_remove_item_quantity():
    cart = Cart()
    cart.add_item("pen", 1.5, quantity=5)
    cart.remove_item("pen", quantity=2)
    assert cart.items() == {"pen":3}

@ pytest.mark.parametrize("qty", [0, -1])
def test_remove_invalid_quantity(qty):
    cart = Cart()
    cart.add_item("book", 10.0)
    with pytest.raises(KeyError):
        cart.remove_item("book", quantity=5)  # remove more than present -> should error? spec not clear

# Subtotal calculation tests

def test_subtotal_bulk_discount():
    cart = Cart()
    cart.add_item("itemA", 10.0, quantity=10)   # 5% bulk discount
    assert cart.subtotal() == round(10.0*10 * (1-0.05),2)

# Total calculation with coupon and member

def test_total_with_coupon_and_member():
    cart = Cart()
    cart.add_item("gift", 200.0)
    # subtotal before discount = 200
    # apply coupon SAVE20 -> 160
    # shipping after coupon: for non-member 60, but since subtotal 200 <1000 so fee 60
    # total expected = 220
    assert cart.total(coupon="SAVE20") == 220.0
    # as member, shipping half of 60 =>30, total=190
    assert cart.total(member=True,coupon="SAVE20") == 190.0

# Empty cart behavior

def test_empty_cart_total():
    cart = Cart()
    assert cart.subtotal() == 0
    assert cart.total() == 0
