import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------
# Helper assertions
# ---------------------

# --------- apply_discount tests ---------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --------- bulk_discount_percent tests ---------

def test_bulk_discount_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --------- parse_coupon tests ---------

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon(' save25 ') == 25
    assert parse_coupon('SaVe1') == 1

@ pytest.mark.parametrize("code", [
    'INVALID',   # missing SAVE
    'SAVE0',     # out of bounds
    'SAVE51',    # out of bounds
    'SAVEXX',    # non-digit
    '123',       # wrong prefix
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --------- shipping_fee tests ---------

def test_shipping_free_for_high_subtotal():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.50) == 0

@ pytest.mark.parametrize("subtotal", [999.99, 500])
def test_regular_and_member(subtotal):
    # regular member
    assert shipping_fee(subtotal) == 60
    # member discount
    assert shipping_fee(subtotal, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --------- Cart tests ---------

def test_cart_empty_total():
    cart = Cart()
    assert cart.total() == 0
    assert cart.total(member=True, coupon=None) == 0


def test_cart_subtotal_and_items():
    c = Cart()
    c.add_item('apple', 1.00, quantity=5)
    c.add_item('banana', 0.50, quantity=12)
    # apples no bulk discount (qty<10) -> 5*1.00=5
    # bananas qty>=10 => 5% off each unit: price after bulk = 0.50*0.95
    banana_total = 12 * 0.50 * 0.95
    expected_subtotal = round(5 + banana_total, 2)
    assert c.subtotal() == expected_subtotal
    assert c.items() == {'apple': 5, 'banana': 12}


def test_cart_add_and_remove_items():
    cart = Cart()
    cart.add_item('item1', 10.0)
    assert cart.items()['item1'] == 1
    cart.remove_item('item1')
    assert cart.items() == {}

    cart.add_item('item2', 5, quantity=3)
    cart.remove_item('item2', quantity=2)
    assert cart.items()['item2'] == 1


def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    # 20 items of $10 each -> bulk discount 15%
    cart.add_item('widget', 10, quantity=20)
    subtotal_before_bulk = 200.0
    discounted_unit = 10 * (1 - 0.15)  # 8.5 per unit
    expected_subtotal = round(20 * discounted_unit, 2)  # 170.0
    assert cart.subtotal() == expected_subtotal

    # Apply a valid coupon 20%
    total_after_coupon = apply_discount(expected_subtotal, 20)
    shipping = shipping_fee(total_after_coupon)
    final_expected = round(total_after_coupon + shipping, 2)
    assert cart.total(coupon='SAVE20') == final_expected

    # Test invalid coupon propagates ValueError
    with pytest.raises(ValueError):
        cart.total(coupon='BADCODE')

# --------- Edge case: member shipping free if subtotal >= 1000 after coupon ----------

def test_cart_shipping_free_for_member():
    cart = Cart()
    # Add items to exceed $1000 after discount but before shipping
    cart.add_item('expensive', 500, quantity=3)  # subtotal 1500
    # Use a big coupon to bring below threshold? Actually shipping free when subtotal>=1000
    assert cart.total(member=True, coupon=None) == round(1500.00 + 30, 2)
    # Using a coupon that reduces subtotal below 1000 -> still charge shipping because rule based on subtotal after coupon.
    with pytest.raises(ValueError):
        # we need to test that if subtotal < 0? not applicable
        pass
