import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- simple functions -----

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

# boundary and error cases for apply_discount
@ pytest.mark.parametrize("price,percent", [
    (-1, 10), (100, -5), (100, 105)
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk discount percents
@ pytest.mark.parametrize("qty,expected", [
    (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount(qty, expected):
    assert bulk_discount_percent(qty) == expected

@ pytest.mark.parametrize("qty", [0,-1,3.5,"a"])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# coupon parsing (case‑insensitive and trimmed)
@ pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10), ("save20",20), (" SAVE30 ",30)
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@ pytest.mark.parametrize("code", ["SAVEXX","SAVE0","SAVE51","ABCD10","SAVE-5"] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping fee
@ pytest.mark.parametrize("subtotal,member,expected", [
    (1001, False,0), (1000, True,0), (500,False,60), (500,True,30),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-10,-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Cart class -----
@pytest.fixture
def cart():
    return Cart()

# add item
@ pytest.mark.parametrize("name,price,qty", [(
    'apple',1.0,2),('banana',0.5,3)])
def test_add_item(cart, name, price, qty):
    cart.add_item(name, price, qty)
    assert cart.items()[name] == qty
    # adding same again increments
    cart.add_item(name, price, 1)
    assert cart.items()[name] == qty+1

# error when different unit_price
def test_add_item_diff_price(cart):
    cart.add_item('orange',1.0,1)
    with pytest.raises(ValueError):
        cart.add_item('orange',2.0,1)

# invalid price or quantity
@ pytest.mark.parametrize("name,price,qty", [('x',-1,1),( 'y',1,-1),('z',1,0)])
def test_add_item_invalid(cart, name, price, qty):
    with pytest.raises(ValueError):
        cart.add_item(name, price, qty)

# remove item
def test_remove_item(cart):
    cart.add_item('mango',2.5,3)
    cart.remove_item('mango',1)
    assert cart.items()['mango']==2
    # remove more than remaining -> removed
    cart.remove_item('mango',5)
    assert 'mango' not in cart.items()

# removing non-existent raises KeyError
def test_remove_nonexistent(cart):
    with pytest.raises(KeyError):
        cart.remove_item('pineapple',1)

# subtotal calculations with bulk discounts
@ pytest.mark.parametrize("items,expected_subtotal", [(
    [('a',10.0,5)],  # no discount: 50
    50.0), (
    [('b',20.0,10)], # 5% discount on that item: 190
    190.0), (
    [('c',5.0,60)], # 10% discount: 270
    270.0), (
    [],
    0.0),
])
def test_subtotal(cart, items, expected_subtotal):
    for name,price,q in items:
        cart.add_item(name,price,q)
    assert cart.subtotal() == round(expected_subtotal,2)

# total with coupon and shipping
@ pytest.mark.parametrize("items,coupon,member,expected_total", [(
    [('item',200.0,1)], None, False, 260.0), # 200 + 60 shipping
    ([("product",1000.0,1)], None, False, 1000.0), # free shipping
    ([('x',500.0,2)], 'SAVE10', True, 930.0) # subtotal 1000, 10% coupon ->900, +30 shipping
])
def test_total(cart, items, coupon, member, expected_total):
    for name,p,q in items:
        cart.add_item(name,p,q)
    assert cart.total(member=member, coupon=coupon) == round(expected_total,2)

# empty cart total is 0
def test_empty_cart_total(cart):
    assert cart.total() == 0.0

# invalid coupon raises ValueError in total
def test_total_invalid_coupon(cart):
    cart.add_item('a',10,1)
    with pytest.raises(ValueError):
        cart.total(coupon='BAD')
