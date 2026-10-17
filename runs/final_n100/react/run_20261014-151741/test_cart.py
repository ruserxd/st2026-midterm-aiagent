import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- Tests for apply_discount -----

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", ["abc", None, -5, 105])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ----- Tests for bulk_discount_percent -----

def test_bulk_discount_quantities():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -1, -5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ----- Tests for parse_coupon -----

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("  SaVe5 ") == 5

@ pytest.mark.parametrize("code", ["SAVEX", "DISCOUNT", "SAVE0", "SAVE51", "SAVE-5", "", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- Tests for shipping_fee -----

def test_shipping_fee_regular_and_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    assert shipping_fee(400, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Tests for Cart -----

def test_cart_empty_total():
    c = Cart()
    assert c.total() == 0
    assert c.items() == []

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("Apple", unit_price=50, quantity=2)
    assert c.subtotal() == 100
    assert len(c.items()) == 1
    name, price, qty = c.items()[0]
    assert name == "Apple"
    assert price == 50
    assert qty == 2


def test_cart_remove_and_quantity():
    c = Cart()
    c.add_item("Banana", unit_price=20, quantity=5)
    c.remove_item("Banana", quantity=3)
    assert c.items()[0][2] == 2
    # remove remaining
    c.remove_item("Banana")
    assert c.items() == []

# Test bulk discount applied per item inside total calculation

def test_cart_bulk_discount_in_total():
    c = Cart()
    c.add_item("Notebook", unit_price=200, quantity=10)  # 5% discount
    # subtotal before coupon: 2000
    assert c.subtotal() == 2000
    total_no_coupon = c.total()
    # shipping fee on 1900 (after 5%) -> 60
    expected = 1900 + 60
    assert total_no_coupon == round(expected, 2)

# Test coupon discount in total

def test_cart_coupon_in_total():
    c = Cart()
    c.add_item("Pen", unit_price=30, quantity=4)  # subtotal 120
    # apply SAVE10 -> 12 discount
    total_with_coupon = c.total(coupon="SAVE10")
    expected_amount = (120 - 12) + 60  # shipping after coupon
    assert total_with_coupon == round(expected_amount, 2)

# Test invalid coupon raises ValueError in Cart.total

def test_cart_invalid_coupon():
    c = Cart()
    c.add_item("Pencil", unit_price=5, quantity=10)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Test member shipping discount through Cart.total

def test_cart_member_shipping_fee_in_total():
    c = Cart()
    c.add_item("Book", unit_price=100, quantity=3)  # subtotal 300
    total_with_member = c.total(member=True)
    expected_amount = 300 + 30  # half shipping fee
    assert total_with_member == round(expected_amount, 2)

# Test rounding of totals

def test_cart_total_rounding():
    c = Cart()
    c.add_item("Item", unit_price=333.33, quantity=3)  # subtotal 999.99
    total = c.total()  # after coupon none; shipping fee 60
    assert total == round(999.99 + 60, 2)
