import re
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -----------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent",[
    (100, 0),
    (0, 50),
])
def test_apply_discount_no_change(price, percent):
    assert apply_discount(price, percent) == round(price * (1 - percent/100.0), 2)

@ pytest.mark.parametrize("price",[-10, -1])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent",[ -5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------------------------------------------

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

@ pytest.mark.parametrize("quantity",[0,-1])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon --------------------------------------------------------

def test_parse_coupon_valid_codes():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save5') == 5
    assert parse_coupon('   SaVe20   ') == 20

@ pytest.mark.parametrize("code",[
    'INVALID',
    'SAVEBIG',
    'SAve0',
    'SAVE51',
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -------------------------------------------------------

def test_shipping_fee_free_and_half():
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    assert shipping_fee(10, member=True) == 30
    assert shipping_fee(1100, member=True) == 0

@ pytest.mark.parametrize("subtotal",[-5,-1])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class --------------------------------------------------------

def test_cart_basic_operations():
    c = Cart()
    assert list(c.items()) == []

    c.add_item('apple', 2.5, quantity=3)
    assert c.subtotal() == 7.5
    # adding same item increases quantity and price stays the same
    c.add_item('apple', 2.5, quantity=2)
    assert list(c.items()) == [('apple', (2.5, 5))]

    c.remove_item('apple', quantity=1)
    assert list(c.items()) == [('apple', (2.5, 4))]
    # remove more than existing quantity removes the item
    c.remove_item('apple', quantity=10)
    assert list(c.items()) == []

def test_cart_total_with_member_and_coupon():
    c = Cart()
    c.add_item('widget', 100, quantity=2)   # subtotal 200
    total_no_discount = c.total(member=True)
    assert total_no_discount == 200 + 30   # shipping fee half for member

    # coupon SAVE10 gives 10% off on items, shipping remains same
    total_coupon = c.total(member=False, coupon='SAVE10')
    expected_items = 200 * 0.9
    expected_total = round(expected_items + 60, 2)
    assert total_coupon == expected_total

# ---------- bulk discount applied in total calculation test (cart class) ------

def test_cart_bulk_discount_in_total():
    c = Cart()
    # 120 units of 'mega' at $10 each => subtotal 1200, bulk discount 15%
    c.add_item('mega', 10, quantity=120)
    total_no_member = c.total(member=False)
    expected_items = 1200 * 0.85
    assert round(total_no_member,2) == round(expected_items + 60,2)

# ---------- coupon case-insensitive test -------------------------------------

def test_parse_coupon_case_insensitivity():
    assert parse_coupon('saVe25') == 25

# ---------- shipping fee edge cases -------------------------------------------

def test_shipping_fee_exact_thresholds():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
