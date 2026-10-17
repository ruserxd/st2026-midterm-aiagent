import pytest
import cart

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    expected = round(123.45 * (1 - 0.10), 2)
    assert cart.apply_discount(123.45, 10) == expected

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5, '10'])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save25') == 25
    assert cart.parse_coupon('  SAVE50 ') == 50
    assert cart.parse_coupon('SaVe1') == 1

@pytest.mark.parametrize("code", [
    'sAVE0',
    'SAVE51',
    'NOPE',
    'SAVEABC',
    'SAVEx10',
    'SAVE 10',
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(999, member=True) == 30
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.5, 3)
    assert c.items() == {'apple': 3}
    # add same item with same price
    c.add_item('apple', 2.5, 1)
    assert c.items() == {'apple': 4}

def test_cart_add_existing_different_price():
    c = cart.Cart()
    c.add_item('banana', 1.0, 2)
    with pytest.raises(ValueError):
        c.add_item('banana', 1.5, 1)

def test_cart_add_invalid_parameters():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('pear', -1.0, 1)
    with pytest.raises(ValueError):
        c.add_item('pear', 1.0, 0)
    with pytest.raises(ValueError):
        c.add_item('pear', 1.0, -3)
    with pytest.raises(ValueError):
        c.add_item('pear', 1.0, 'two')

def test_cart_remove():
    c = cart.Cart()
    c.add_item('orange', 3.0, 5)
    c.remove_item('orange', 2)
    assert c.items() == {'orange': 3}
    # remove remaining and more
    c.remove_item('orange', 4)  # should remove the item
    assert 'orange' not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item('item1', 5.0, 2)   # 10
    c.add_item('item2', 3.5, 1)   # 3.5
    assert c.subtotal() == 13.5

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

@pytest.mark.parametrize("member,coupon,total_expected", [
    (False, None, 70.0),
    (True, None, 40.0),
    (False, 'SAVE20', 68.0),
    (True, 'SAVE20', 38.0),
])
def test_cart_total_variants(member, coupon, total_expected):
    c = cart.Cart()
    c.add_item('item', 5.0, 2)  # subtotal 10
    if coupon:
        total = c.total(member=member, coupon=coupon)
    else:
        total = c.total(member=member)
    assert total == total_expected

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item('item', 5.0, 2)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')

def test_cart_total_rounding():
    # subtotal: 19.99 *1
    # coupon 33% = discounted amount = 19.99 * 0.67 = 13.3933
    # shipping 60 -> total 73.3933, round to 73.39
    c = cart.Cart()
    c.add_item('product', 19.99, 1)
    assert c.total(coupon='SAVE33') == 73.39
