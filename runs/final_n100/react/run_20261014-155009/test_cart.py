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

@ pytest.mark.parametrize("price,percent", [(-1,10), (100,-5)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------------------

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon --------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  Save5 ") == 5

@ pytest.mark.parametrize("code", ["SAVEX", "save0", "save51", "invalid", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart ------------------------------------------------------------

def test_cart_basic_flow():
    cart = Cart()
    cart.add_item("apple", 100, quantity=2)   # subtotal 200
    cart.add_item("banana", 50)               # subtotal 250
    assert cart.subtotal() == 250
    total_without_coupon = cart.total(member=False)
    # No coupon: shipping_fee on 250 is 60 -> 310
    assert total_without_coupon == 310.0


def test_cart_with_member_and_bulk_discount():
    cart = Cart()
    cart.add_item("widget", 200, quantity=10)  # bulk discount 5% on each item price? actually applies to entire subtotal?
    # Subtotal = 200*10 = 2000
    assert cart.subtotal() == 2000
    # Bulk discount percent for 10 units is 5
    discounted_subtotal = apply_discount(2000, bulk_discount_percent(10))
    # Shipping fee on discounted amount: shipping_fee(discounted_subtotal)
    expected_total = round(discounted_subtotal + shipping_fee(discounted_subtotal, member=True), 2)
    assert cart.total(member=True) == expected_total


def test_cart_with_coupon_and_member():
    cart = Cart()
    cart.add_item("gadget", 400)
    total = cart.total(member=True, coupon="SAVE10")
    # subtotal=400; coupon discount=40; after discount=360; shipping half fee 30
    assert total == 390.0


def test_cart_empty_no_shipping():
    cart = Cart()
    assert cart.subtotal() == 0
    assert cart.total(member=True, coupon=None) == 0.0
    assert cart.total(member=False, coupon=None) == 0.0

# ---------- Error handling in Cart methods ---------------------------------

def test_cart_add_negative_price():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", -5)

@ pytest.mark.parametrize("quantity", [0, -1])
def test_cart_add_invalid_quantity(quantity):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("foo", 10, quantity=quantity)

# ---------- remove_item behavior ------------------------------------------

def test_cart_remove_and_total():
    cart = Cart()
    cart.add_item("item1", 100, quantity=3)  # subtotal 300
    cart.remove_item("item1", quantity=2)     # remaining 1*100
    assert cart.subtotal() == 100
    assert cart.total() == round(100 + shipping_fee(100), 2)
