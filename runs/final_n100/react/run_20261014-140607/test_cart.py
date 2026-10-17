import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# -- function specs ---------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # round to two decimals
    assert apply_discount(99.999, 10) == 90.00

@ pytest.mark.parametrize("price,percent",[
    (-1,10), (50,-5), (50,105)
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk discount tests

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# parse_coupon tests

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('  save20  ') == 20
    # case-insensitive
    assert parse_coupon('SaVe30') == 30

@ pytest.mark.parametrize("code", ["INVALID", "SAVEXY", "SAVE0", "SAVE51"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests

def test_shipping_fee():
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60

assert shipping_fee(1000) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart class tests ---------------------------------------------

@pytest.fixture
def cart():
    return Cart()

def test_add_item_basic(cart):
    cart.add_item('apple', 10, 2)
    assert cart.items() == {'apple': 2}
    # adding same item increases quantity
    cart.add_item('apple', 10, 3)
    assert cart.items()['apple'] == 5

# test unit price mismatch raises ValueError

def test_add_item_price_mismatch(cart):
    cart.add_item('banana', 5, 1)
    with pytest.raises(ValueError):
        cart.add_item('banana', 6, 2)

# remove item tests

def test_remove_item_basic(cart):
    cart.add_item('orange', 3, 4)
    cart.remove_item('orange', 2)
    assert cart.items()['orange'] == 2

# removing more than available should delete item

def test_remove_item_over_removal(cart):
    cart.add_item('kiwi', 2, 1)
    cart.remove_item('kiwi', 2)  # expect deletion due to quantity <=0
    assert 'kiwi' not in cart.items()

# removing non-existent item raises KeyError

def test_remove_item_missing(cart):
    with pytest.raises(KeyError):
        cart.remove_item('pineapple')

# subtotal calculations

def test_subtotal(cart):
    cart.add_item('item1', 20, 9)   # no discount
    cart.add_item('item2', 10, 10)  # 5% bulk
    # item1: 180, no discount -> 180
    # item2: 100 with 5% -> 95
    assert cart.subtotal() == round(180 + 95, 2)

# total with member and coupon

def test_total(cart):
    cart.add_item('tshirt', 200, 1)  # subtotal 200
    # no coupon or membership: shipping 60 -> 260
    assert cart.total() == 260.0
    # member: shipping 30 -> 230
    assert cart.total(member=True) == 230.0
    # with valid coupon 10% off before shipping
    amount_after_coupon = apply_discount(200, 10)
    expected = round(amount_after_coupon + shipping_fee(200, False), 2)
    assert cart.total(coupon='SAVE10') == expected

# test total on empty cart returns 0

def test_total_empty():
    c = Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon='SAVE5') == 0
