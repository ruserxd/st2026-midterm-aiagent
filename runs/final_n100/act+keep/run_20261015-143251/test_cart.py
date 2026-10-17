import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Helper for approximate equality

def approx(value):
    return round(value, 2)

# --- apply_discount tests ---

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent,expected", [
    (100, 0, 100.0),
    (100, 100, 0.0),
    (123.45, 10, 111.11),  # 123.45*0.9=111.105 -> 111.11
])
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (30, 120)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --- bulk_discount_percent tests ---

def test_bulk_discount_percent_basic():
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent_ranges(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --- parse_coupon tests ---

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save25 ') == 25
    assert parse_coupon(' SAVE50') == 50

@ pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "BADCODE", "s ave5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee tests ---

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal,member,expected", [
    (200, False, 60),
    (200, True, 30),
    (1200, False, 0),
    (1200, True, 0),
])
def test_shipping_fee_members(subtotal, member, expected):
    # Shipping fee ignores member flag in spec? Actually only halves for members
    if subtotal < 1000:
        assert shipping_fee(subtotal, member) == expected
    else:
        assert shipping_fee(subtotal, member) == 0

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart tests ---

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == []
    assert c.subtotal() == 0.0
    assert c.total() == 0


def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item('apple', 5, quantity=3)
    c.add_item('banana', 2)
    assert c.items() == [('apple', 5.0, 3), ('banana', 2.0, 1)]
    assert c.subtotal() == 5*3 + 2
    c.remove_item('apple')
    assert c.items() == [('banana', 2.0, 1)]
    c.remove_item('banana', quantity=1)
    assert c.items() == []


def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item('widget', 200, quantity=10)  # subtotal 2000
    # coupon SAVE10 => 10% off subtotal -> 1800
    assert c.total(coupon='SAVE10') == approx(1800.0)
    # no shipping because subtotal >=1000 after discount? yes free
    c = Cart()
    c.add_item('gadget', 300, quantity=3)  # subtotal 900
    # coupon SAVE5 => 5% off -> 855; shipping fee 60 (non-member)
    assert c.total(coupon='SAVE5') == approx(915.0)
    # member gets half shipping: 30
    assert c.total(member=True, coupon='SAVE5') == approx(885.0)


def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item('item', 10)
    with pytest.raises(ValueError):
        c.total(coupon='BADCODE')

# Ensure rounding behavior for totals

def test_cart_total_rounding():
    c = Cart()
    c.add_item('pricey', 123.456, quantity=1)
    # No coupon, subtotal 123.456; shipping 60 -> total 183.456 rounded 183.46
    assert c.total() == approx(183.46)
