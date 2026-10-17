import pytest
import cart

# Helper to round for comparison
ROUND = lambda x: round(float(x), 2)

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == ROUND(expected)

@pytest.mark.parametrize("price,percent", [(-1,10),(10,-5),(10,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("qty,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("code,expected", [
    ('SAVE10',10),
    ('save5',5),
    ('  SaVe25 ',25),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ['abc','SAve0','SAVe51','SAVE-10',''])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart behavior tests

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item('apple', unit_price=1, quantity=3)
    c.add_item('banana', unit_price=2, quantity=2)
    # Adding existing item increases qty only if price matches
    c.add_item('apple', unit_price=1, quantity=2)
    assert c.items() == {'apple':5,'banana':2}
    # subtotal with no bulk discount yet: 5*1 + 2*2 = 9.0
    assert c.subtotal() == 9.0
    # remove some apples
    c.remove_item('apple', quantity=3)
    assert c.items() == {'apple':2,'banana':2}
    # subtotal: 2*1 + 2*2 = 6.0
    assert c.subtotal() == 6.0
    # remove more to zero out bananas
    c.remove_item('banana', quantity=2)
    assert 'banana' not in c.items()
    # removing nonexistent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item('cherry')

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item('orange', unit_price=3)
    with pytest.raises(ValueError):
        c.add_item('orange', unit_price=4)

@pytest.mark.parametrize("qty,expected_subtotal", [
    # 9 apples => no bulk discount: 9*1 = 9
    (9,9),
    # 10 apples => 5% bulk: 10*1 *0.95 = 9.5
    (10,9.5),
    (50, 45.0),   # 10% discount on each of 50 -> 50*0.90=45
    (100, 85.0),  # 15% discount -> 100*0.85=85
])
def test_cart_subtotal_with_bulk(qty, expected_subtotal):
    c = cart.Cart()
    c.add_item('item', unit_price=1, quantity=qty)
    assert round(c.subtotal(),2) == ROUND(expected_subtotal)

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # 20 units -> bulk discount 10% -> subtotal 18
    c.add_item('prod', unit_price=1, quantity=20)
    # subtotal after bulk
    assert round(c.subtotal(),2) == 18.0
    # apply coupon SAVE10: reduce by 10%
    total_after_coupon = cart.apply_discount(18.0, 10)
    # shipping fee on this amount (non-member): 60
    expected_total = round(total_after_coupon + 60, 2)
    assert c.total(coupon='SAVE10') == expected_total
    # member should get half shipping
    expected_member = round(total_after_coupon + 30, 2)
    assert c.total(member=True, coupon='save10') == expected_member
    # no coupon and member
    expected_no_coupon = round(18.0 + 30, 2)
    assert c.total(member=True) == expected_no_coupon
    # empty cart costs 0 (no shipping)
    e = cart.Cart()
    assert e.total() == 0.0
