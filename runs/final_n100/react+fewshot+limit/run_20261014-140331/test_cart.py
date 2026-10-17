import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (99, 10),
    (50, 10),
    (49, 5),
    (10, 5),
    (9, 0),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    (" SAVE30", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",  # missing E
    "SAVE0",  # out of range
    "SAVE51",
    "BADCODE",
    "SAVE-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart functionality
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.0, 3)
    assert c.items() == {'apple': 3}
    # add same item increments quantity and requires same unit_price
    c.add_item('apple', 2.0, 2)
    assert c.items() == {'apple': 5}
    with pytest.raises(ValueError):
        c.add_item('apple', 1.5, 1)

def test_cart_remove():
    c = cart.Cart()
    c.add_item('banana', 1.0, 4)
    c.remove_item('banana', 2)
    assert c.items() == {'banana': 2}
    # remove remaining to zero
    c.remove_item('banana', 2)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item('banana', 1)

def test_cart_subtotal_and_bulk_discount():
    c = cart.Cart()
    # 5 units no discount
    c.add_item('x', 10.0, 5)
    assert c.subtotal() == 50.0
    # 10 units gets 5% bulk discount on that item
    c.add_item('y', 20.0, 10)
    # y subtotal before discount: 200 -> after 5% = 190
    expected_subtotal = round(50 + 190, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('item', 100.0, 1)
    # subtotal 100
    # apply coupon SAVE10 -> 90
    total = c.total(coupon='SAVE10')
    assert total == round(90 + 60, 2)  # shipping fee 60

def test_cart_total_member_and_no_shipping():
    c = cart.Cart()
    c.add_item('expensive', 1000.0, 1)
    # subtotal 1000, coupon none, shipping free
    assert c.total(member=True) == 1000.0

# Edge case: empty cart total is 0 and no shipping
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
