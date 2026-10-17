import pytest
import cart

# Helper functions for tests

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-10, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,percent", [
    (99, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -5, 3.2, "10"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

valid_coupons = {
    'SAVE10': 10,
    'save25': 25,
    '  SaVe50  ': 50,
}
@pytest.mark.parametrize("code,expected", list(valid_coupons.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_coupons = ['SAV10', 'SAVE0', 'SAVE51', 'FOO10', ' SAVE -5 ', '']
@pytest.mark.parametrize("code", invalid_coupons)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,fee", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item('apple', 2.0, 3)
    assert c.items() == {'apple': 3}
    c.add_item('apple', 2.0, 2)
    assert c.items() == {'apple': 5}
    with pytest.raises(ValueError):
        c.add_item('apple', 3.0)

def test_cart_remove():
    c = cart.Cart()
    c.add_item('banana', 1.5, 4)
    c.remove_item('banana')
    assert c.items() == {'banana': 3}
    c.remove_item('banana', quantity=3)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item('orange')

def test_cart_subtotal():
    c = cart.Cart()
    assert c.subtotal() == 0
    c.add_item('widget', 10.0, 9)
    assert c.subtotal() == 90.0
    c.add_item('gadget', 20.0, 10)
    expected = round(10*9 + cart.apply_discount(20*10, 5), 2)
    assert c.subtotal() == expected

def test_cart_total():
    c = cart.Cart()
    c.add_item('item', 100.0, 1)
    subtotal = 100.0
    shipping = cart.shipping_fee(subtotal)
    assert c.total() == round(subtotal + shipping, 2)
    amount_after_coupon = cart.apply_discount(subtotal, 10)
    expected_total = round(amount_after_coupon + cart.shipping_fee(subtotal), 2)
    assert c.total(coupon='SAVE10') == expected_total
    assert c.total(member=True) == round(subtotal + 30.0, 2)
    empty = cart.Cart()
    assert empty.total() == 0

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item('item', 50.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')
