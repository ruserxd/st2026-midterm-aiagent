import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- Helper functions for expected values from spec ----------

def round_two(x):
    return round(float(x), 2)

# tests for apply_discount
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (123.45, 10, 111.11), # 123.45 - 12.345 = 111.105 -> rounded to 111.11
])
def test_apply_discount(price, percent, expected):
    assert round_two(apply_discount(price, percent)) == expected

@pytest.mark.parametrize("price,percent", [(-1,10),(100,-5),(100,101)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0,-1,3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ('SAVE10',10),('save20','20'),('  SaVe30  ','30'),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == int(expected)

@pytest.mark.parametrize("code", ['INVALID', 'SAVE0', 'SAVE51', 'SAVEB'] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000,False,0),
    (999.99,False,60),
    (500,True,30),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# tests for Cart class

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == {}
    # add items
    cart.add_item('apple', 100, 5)
    cart.add_item('banana', 200)
    assert cart.items() == {
        'apple': (100, 5),
        'banana': (200, 1),
    }
    # subtotal calculation
    assert cart.subtotal() == 100*5 + 200
    # remove item partially
    cart.remove_item('apple', 2)
    assert cart.items()['apple'][1] == 3
    # remove all of an item
    cart.remove_item('banana')
    assert 'banana' not in cart.items()
    # total without discounts
    subtotal = cart.subtotal()
    total_expected = subtotal + shipping_fee(subtotal)
    assert cart.total() == round_two(total_expected)

@pytest.mark.parametrize("quantity,expected", [
    (5,0),
    (10,5),
])
def test_cart_bulk_discount(quantity, expected):
    cart = Cart()
    cart.add_item('widget', 100, quantity)
    # subtotal includes bulk discount
    unit_price_with_discount = apply_discount(100, bulk_discount_percent(quantity))
    subtotal_expected = unit_price_with_discount * quantity
    assert cart.subtotal() == round_two(subtotal_expected)

@pytest.mark.parametrize("coupon,expected", [
    ('SAVE10',10),('  save5 ','5'),
])
def test_cart_coupon_and_member(coupon, expected):
    cart = Cart()
    cart.add_item('item', 200)
    subtotal = cart.subtotal()
    total_no_discount = round_two(subtotal + shipping_fee(subtotal))
    # member discount 5% plus coupon
    member_discount = apply_discount(total_no_discount, 5)
    final_expected = apply_discount(member_discount, expected)
    assert cart.total(member=True, coupon=coupon) == round_two(final_expected)

# Ensure invalid coupon raises ValueError when passed to total

def test_cart_invalid_coupon():
    cart = Cart()
    cart.add_item('item', 100)
    with pytest.raises(ValueError):
        cart.total(coupon='BADCODE')
