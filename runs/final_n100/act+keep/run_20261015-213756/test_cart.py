"""
# test_cart.py
import pytest
import cart

# Helper function to round as spec expects
from decimal import Decimal

def round2(value):
    return round(float(Decimal(str(value))), 2)

# ---------- Function Tests ----------

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# negative price raises
@ pytest.mark.raises(ValueError)
def test_apply_discount_negative_price():
    cart.apply_discount(-1, 10)

# percent out of bounds
@pytest.mark.parametrize("price,percent", [
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (1,0),
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0,-5,2.3])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon
valid_coupons = {
    'SAVE10': 10,
    'save20': 20,
    '  SaVe5  ': 5,
}
@pytest.mark.parametrize("code,expected", list(valid_coupons.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_coupons = ["SAV10", "SAVE-5", "save0", "save51", "foo"]
@pytest.mark.parametrize("code", invalid_coupons)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-1)

# ---------- Cart class Tests ----------

def test_cart_initialization():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# add_item and items

def test_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 1.0, 3)
    assert c.items() == {'apple': 3}
    c.add_item('banana', 2.5, 2)
    assert c.items() == {'apple': 3, 'banana': 2}

# adding same item increases quantity and price must match

def test_add_same_item_increase_and_price_mismatch():
    c = cart.Cart()
    c.add_item('apple', 1.0, 1)
    c.add_item('apple', 1.0, 2)
    assert c.items() == {'apple': 3}
    with pytest.raises(ValueError):
        c.add_item('apple', 1.5, 1)

# subtotal calculation with bulk discount

def test_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item('item', 10.0, 12)  # 5% bulk
    expected = 10.0 * 12 * (1 - 0.05)
    assert round2(c.subtotal()) == round2(expected)

# remove_item behavior

def test_remove_item():
    c = cart.Cart()
    c.add_item('item', 5.0, 4)
    c.remove_item('item', 1)
    assert c.items() == {'item': 3}
    c.remove_item('item', 3)  # should remove entirely
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

# total calculation including coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('item', 200.0, 5)   # no bulk discount
    subtotal = 200 * 5
    assert round2(c.subtotal()) == round2(subtotal)
    total_no_coupon = subtotal + cart.shipping_fee(subtotal, False)
    assert round2(c.total(member=False)) == round2(total_no_coupon)
    # apply coupon 10%
    after_coupon = subtotal * (1 - 0.10)
    expected_total = after_coupon + cart.shipping_fee(after_coupon, False)
    assert round2(c.total(member=False, coupon='SAVE10')) == round2(expected_total)

# total with member discount on shipping

def test_total_member_shipping_discount():
    c = cart.Cart()
    c.add_item('item', 200.0, 5)
    subtotal = 200 * 5
    after_coupon = subtotal
    expected_total = after_coupon + cart.shipping_fee(after_coupon, True)
    assert round2(c.total(member=True)) == round2(expected_total)

# empty cart total zero no shipping

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0

"""
