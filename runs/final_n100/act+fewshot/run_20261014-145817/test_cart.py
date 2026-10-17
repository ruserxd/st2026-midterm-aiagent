import pytest
import cart

# Helper to round floats as spec uses 2 decimals

def approx(value, expected):
    return abs(value - expected) < 1e-9

# apply_discount tests
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price, percent) == result

# invalid price/percent
@pytest.mark.parametrize("price,percent",[
    (-10,10),
    (10,-5),
    (10,150)
])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(qty,expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty",[0,-1,3.5,'a'])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected",[
    ('SAVE10',10),('save20','20'),('  SaVe5  ',5),
])
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code",['save0','SAve51','ABCD',''])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected",[
    (500,False,60),
    (1000,True,0),
    (999.99,False,60),
    (1000,False,0),
    (2000,True,0)
])
def test_shipping_fee(subtotal,member,expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal",[-1,-0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item('apple', 2.0, 3)
    assert c.items() == {'apple':3}
    # add same item increases quantity
    c.add_item('apple', 2.0, 2)
    assert c.items() == {'apple':5}
    # adding different price raises ValueError
    with pytest.raises(ValueError):
        c.add_item('apple', 3.0, 1)

def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item('banana', 1.5, 4)
    c.remove_item('banana', 2)
    assert c.items() == {'banana':2}
    # remove remaining
    c.remove_item('banana', 2)
    assert c.items() == {}
    # removing non-existing raises KeyError
    with pytest.raises(KeyError):
        c.remove_item('orange',1)

# subtotal and total calculations

def test_cart_subtotal_and_total_no_discounts():
    c = cart.Cart()
    c.add_item('x', 10, 2)   # 20
    c.add_item('y', 5, 3)    # 15
    assert c.subtotal() == 35.0
    assert c.total() == 35.0 + 60  # shipping fee


def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item('item', 100, 5)   # subtotal 500
    # coupon SAVE20 => 20% discount on items only? spec not explicit but assume applied to subtotal before shipping
    total = c.total(member=True, coupon='SAVE20')
    # subtotal after coupon: 500 * 0.8 = 400
    # shipping fee for member: 30
    assert total == 430.0

# bulk discount applied per item quantity in total calculation? test

def test_cart_bulk_discount_in_total():
    c = cart.Cart()
    c.add_item('bulk', 10, 120)   # 120 units, unit price 10
    # expected subtotal after bulk discount: 120 * 10 * (1-0.15)=1020
    total = c.total()
    assert total == 1020.0 + 60  # shipping fee
