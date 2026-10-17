import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ----------------------------
# Tests for helper functions
# ----------------------------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(123.45, 10) == round(123.45 * 0.9, 2)

@ pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk_discount_percent

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save20') == 20
    assert parse_coupon(' SAVE30 ') == 30

@ pytest.mark.parametrize("code", ['SA', 'SAVEX', 'SAVE-5', 'SAVE101', '', 'ABC10'])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0


def test_shipping_fee_member():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----------------------------
# Tests for Cart class
# ----------------------------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 60  # shipping fee for empty cart (subtotal 0, non-member)


def test_add_and_remove_items():
    cart = Cart()
    cart.add_item('apple', 2.5)
    assert cart.items()['apple'] == (2.5, 1)
    cart.add_item('apple', 2.5, quantity=3)
    assert cart.items()['apple'] == (2.5, 4)

    # remove part of quantity
    cart.remove_item('apple', quantity=2)
    assert cart.items()['apple'] == (2.5, 2)

    # removing all removes the key
    cart.remove_item('apple', quantity=2)
    assert 'apple' not in cart.items()


def test_subtotal_and_total():
    cart = Cart()
    cart.add_item('widget', 100, quantity=5)   # subtotal 500
    assert cart.subtotal() == 500
    # no discount, member false
    assert cart.total(member=False, coupon=None) == 560  # 500 + 60 shipping

    # apply bulk discount (10% for qty>=50)
    cart.add_item('gadget', 20, quantity=50)   # subtotal additional 1000
    assert cart.subtotal() == 1500
    # total should include 15% bulk discount on gadget only? spec unclear but we'll test percent logic only
    # Let's test coupon application separately
    assert cart.total(member=False, coupon='SAVE10') == 1485.0  # subtotal 1500 -10% = 1350 + shipping 60


def test_coupon_and_member_combination():
    cart = Cart()
    cart.add_item('book', 200)
    # member discount half shipping
    assert cart.total(member=True, coupon=None) == 200 + 30
    # apply valid coupon
    assert cart.total(member=False, coupon='SAVE15') == 200 * 0.85 + 60

# Negative test: invalid coupon raises ValueError in total

def test_total_invalid_coupon():
    cart = Cart()
    cart.add_item('pen', 5)
    with pytest.raises(ValueError):
        cart.total(coupon='INVALID')
