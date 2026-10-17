import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (0, 0),
    (100, 100),
    (50, 10),
])
def test_apply_discount_edge_cases(price, percent):
    result = apply_discount(price, percent)
    expected = round(price * (1 - percent / 100), 2)
    assert result == expected

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 50)

@pytest.mark.parametrize("percent", [101, -1, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("   SaVe5") == 5

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVExx", "NOTACODE", "SA V100"])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee_free_and_half():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0
    # member discount
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart.total ------------------------------------------------------

def test_cart_total_empty_and_no_coupon():
    cart = Cart()
    assert cart.total() == 0.0

def test_cart_total_simple_items_no_shipping():
    cart = Cart()
    cart.add_item("apple", 100, quantity=10)  # subtotal 1000 - free shipping
    assert cart.subtotal() == 1000
    assert cart.total() == 1000.00

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("banana", 50, quantity=10)  # subtotal 500
    total_no_coupon = cart.total()  # should be 500 + shipping 60 = 560
    assert total_no_coupon == 560.00
    # apply coupon 20%
    total_with_coupon = cart.total(coupon="SAVE20")
    # subtotal after coupon: 500 * 0.8 = 400
    # shipping on 400 is 60 - 460
    assert total_with_coupon == 460.00

def test_cart_total_member_shipping_half():
    cart = Cart()
    cart.add_item("item", 200, quantity=5)  # subtotal 1000 free shipping
    assert cart.total(member=True) == 1000.00
    # smaller amount
    cart2 = Cart()
    cart2.add_item("item", 30, quantity=10)  # subtotal 300
    total_non_member = cart2.total()  # 300 + 60 = 360
    total_member = cart2.total(member=True)  # 300 + 30 = 330
    assert total_non_member == 360.00
    assert total_member == 330.00

# ---------- Cart add/remove and items -------------------------------------

def test_cart_add_and_remove():
    cart = Cart()
    cart.add_item("widget", 25, quantity=2)
    cart.add_item("gadget", 15, quantity=1)
    assert len(cart.items()) == 2
    # remove one widget
    cart.remove_item("widget")
    assert cart.items()["widget"]['quantity'] == 1
    # remove remaining widget
    cart.remove_item("widget", quantity=1)
    assert "widget" not in cart.items()
    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")

# ---------- bulk_discount usage in Cart? (not part of spec but test for bug) ---

def test_bulk_discount_not_applied_in_cart():
    cart = Cart()
    cart.add_item("item", 10, quantity=20)
    assert cart.subtotal() == 200
    assert cart.total(coupon="SAVE5") == 190.0  # 5% off subtotal before shipping
