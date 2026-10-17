import pytest
import cart
from decimal import Decimal, ROUND_HALF_UP

def round2(x):
    return float(Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# apply_discount tests

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert round2(cart.apply_discount(123.45, 5)) == round2(117.2775)

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-0.1, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests

def test_bulk_discount_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save5 ') == 5
    assert cart.parse_coupon('  SaVe50   ') == 50

@ pytest.mark.parametrize("code", ['SAVEX', 'SAVE0', 'SAVE51', '10SAVE', '', '  '])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(0, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == []
    c.add_item('apple', 2.5, quantity=3)
    assert c.items() == [{'name': 'apple', 'unit_price': 2.5, 'quantity': 3}]

def test_cart_remove_and_subtotal():
    c = cart.Cart()
    c.add_item('banana', 1.0, quantity=5)
    c.remove_item('banana', quantity=2)
    assert c.items() == [{'name': 'banana', 'unit_price': 1.0, 'quantity': 3}]
    assert round2(c.subtotal()) == round2(3.0)

@ pytest.mark.parametrize("member", [True, False])
def test_cart_total_no_coupon(member):
    c = cart.Cart()
    c.add_item('item', 200, quantity=10)  # subtotal 2000 -> free shipping
    assert round2(c.total(member=member)) == round2(2000)

@ pytest.mark.parametrize("member", [True, False])
def test_cart_total_with_coupon_and_bulk_discount(member):
    c = cart.Cart()
    c.add_item('widget', 100, quantity=12)  # bulk discount applies (10%)
    subtotal_before = 1200
    expected_subtotal_after_bulk = round2(subtotal_before * (1 - 0.10))
    total_with_coupon = round2(expected_subtotal_after_bulk * (1 - 0.20))  # coupon SAVE20
    assert c.total(member=member, coupon='SAVE20') == pytest.approx(total_with_coupon)

def test_integration_scenario():
    c = cart.Cart()
    c.add_item('tshirt', 500, quantity=2)   # subtotal 1000, free shipping
    c.add_item('jeans', 1200, quantity=1)
    assert c.total(coupon='SAVE10') == pytest.approx(2880)
