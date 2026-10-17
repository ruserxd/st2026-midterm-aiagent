import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# --- apply_discount tests ---

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [ -1 , -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --- bulk_discount_percent tests ---

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# --- parse_coupon tests ---

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save20') == 20
    assert parse_coupon('  SaVe30  ') == 30

@ pytest.mark.parametrize("code", ['SAV5', 'SAVE0', 'SAVE51', 'NOTVALID', ''])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee tests ---

def test_shipping_fee():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=False) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart tests ---

def test_cart_basic_operations():
    cart = Cart()
    cart.add_item('apple', 2.5, quantity=4)   # subtotal 10
    cart.add_item('banana', 1.0)
    assert cart.subtotal() == pytest.approx(11.5)
    # member discount applies to total only via total()
    assert cart.total(member=True) == pytest.approx(11.5 * 0.9 + shipping_fee(11.5, member=True))

    cart.remove_item('apple', quantity=2)
    assert cart.subtotal() == pytest.approx(6.5)
    # removing more than present removes item entirely
    cart.remove_item('banana')
    assert 'banana' not in cart.items()


def test_cart_bulk_and_coupon():
    cart = Cart()
    cart.add_item('widget', 100, quantity=120)   # bulk discount 15%
    subtotal = 100 * 120
    expected_subtotal = apply_discount(subtotal, 15)
    assert cart.subtotal() == pytest.approx(expected_subtotal)

    total_before_coupon = cart.total(member=False)
    coupon_code = 'SAVE20'
    total_after = cart.total(coupon=coupon_code, member=False)
    # coupon applies to subtotal after bulk discount and before shipping
    expected_total = apply_discount(cart.subtotal(), 20) + shipping_fee(cart.subtotal())
    assert total_after == pytest.approx(expected_total)
    # member and coupon together
    total_member_coupon = cart.total(member=True, coupon=coupon_code)
    assert total_member_coupon == pytest.approx(apply_discount(total_before_coupon, 0))   # discount already applied

# --- ensure items dictionary integrity ---

def test_cart_items_immutability():
    cart = Cart()
    cart.add_item('bread', 3)
    d = cart.items()
    d['bread'] = (10, 1)  # mutate copy
    assert cart.items()['bread'][0] == 3   # original unchanged
