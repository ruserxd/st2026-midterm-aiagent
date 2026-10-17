import pytest
import cart

# 1 apply_discount tests
@pytest.mark.parametrize('price, percent, expected', [
    (200, 15, 170.0),
    (123.45, 5, 117.28),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize('price', [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize('percent', [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# 2 bulk_discount_percent tests
@pytest.mark.parametrize('quantity, expected', [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # boundary bug expected to fail
    (51, 10),
    (99, 10),
    (100, 15),
    (101, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize('quantity', [0, -1])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# 3 parse_coupon tests
@pytest.mark.parametrize('code, percent', [
    ('SAVE10', 10),
    ('save20', 20),   # case-insensitive bug expected to fail
    ('  SAVE30 ', 30),
    ('SaVe1', 1),     # mixed-case bug expected to fail
    ('SAVE50', 50)
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize('code', ['DISCOUNT10','SAVE0','SAVE51','SAVEX','','   '])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize('code', [None, 123, []])
def test_parse_coupon_non_string_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# 4 shipping_fee tests
@pytest.mark.parametrize('subtotal, member, expected', [
    (999, False, 60),
    (999, True, 30),
    (1000, False, 0),
    (1000, True, 0),
    (1500, False, 0),
    (500, False, 60),
    (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize('subtotal', [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# 5 Cart tests
def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c, cart.Cart)
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_and_subtotal():
    c = cart.Cart()
    c.add_item('apple', 100, quantity=3)
    assert c.items() == {'apple': 3}
    assert c.subtotal() == 300.0
    # shipping fee should be 60 -> total 360
    assert c.total() == 360.0

def test_add_bulk_discount_and_total():
    c = cart.Cart()
    c.add_item('apple', 100, quantity=3)
    c.add_item('banana', 200, quantity=10)   # bulk discount percent 5%
    assert c.subtotal() == 2200.0
    # shipping free for subtotal >= 1000 -> no fee
    assert c.total() == 2200.0

def test_add_existing_item_increments():
    c = cart.Cart()
    c.add_item('apple', 100, quantity=3)
    c.add_item('apple', 100, quantity=2)
    assert c.items() == {'apple': 5}
    assert c.subtotal() == 500.0

def test_add_existing_item_different_price_raises():
    c = cart.Cart()
    c.add_item('apple', 100, quantity=1)
    with pytest.raises(ValueError):
        c.add_item('apple', 150, quantity=1)

def test_remove_item_partial_and_full():
    c = cart.Cart()
    c.add_item('apple', 100, quantity=5)
    c.remove_item('apple', 2)
    assert c.items() == {'apple': 3}
    assert c.subtotal() == 300.0
    c.remove_item('apple', 3)  # remove remaining 3
    # Item should be removed entirely
    assert 'apple' not in c.items()

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('banana')

# 6 total with coupon and shipping fee bug tests
def test_total_with_coupon_and_shipping_fee_bug():
    # original subtotal 1200 >1000, after 20% discount => 960
    c = cart.Cart()
    c.add_item('item', 200, quantity=6)
    result = c.total(coupon='SAVE20')
    assert result == 1020.0   # expected shipping fee applied on discounted amount

def test_total_with_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('item', 100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')

def test_total_member_and_coupon_shipping_fee_bug():
    c = cart.Cart()
    c.add_item('item', 200, quantity=6)
    result = c.total(member=True, coupon='SAVE20')
    assert result == 990.0   # discounted 960 + shipping fee 30

def test_total_no_coupon_free_shipping():
    c = cart.Cart()
    c.add_item('item', 200, quantity=6)
    assert c.total() == 1200.0
