import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# edge cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity, expected", [
    (5, 0),
    (10, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# edge case: non-positive quantity
@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "XYZ", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (1200, False, 0.0),
    (1000, True, 0.0),
    (999, False, 60.0),
    (999, True, 30.0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.5, 3)
    assert c.items() == {'apple': (2.5, 3)}
    # adding same item increases quantity
    c.add_item('apple', 2.5, 2)
    assert c.items() == {'apple': (2.5, 5)}

def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item('banana', 1.0, 4)
    c.remove_item('banana', 2)
    assert c.items() == {'banana': (1.0, 2)}
    # removing more than existing quantity removes item
    c.remove_item('banana', 3)
    assert 'banana' not in c.items()

def test_cart_subtotal_and_total():
    c = cart.Cart()
    c.add_item('item1', 10.0, 2)   # subtotal 20
    c.add_item('item2', 5.0, 4)    # subtotal +20 => 40
    assert c.subtotal() == 40.0
    # total without membership or coupon: shipping 60 (subtotal<1000)
    assert c.total() == 100.0   # 40 + 60 = 100

def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item('item', 20, 10)  # quantity 10 => bulk discount 5%
    subtotal = 200 * 0.95  # after bulk discount applied to each item? assume total
    # but for simplicity assume shipping free because subtotal >=1000? not
    assert c.total(member=True, coupon='SAVE20') == pytest.approx(240) # expecting member fee + coupon discount
