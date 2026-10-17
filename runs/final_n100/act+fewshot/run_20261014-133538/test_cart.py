import pytest
import cart

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == pytest.approx(result)

# error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (200,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error cases bulk_discount_percent
@pytest.mark.parametrize("quantity", [0,-1,3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity,int) else cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    (" save20 ",20),
    ("SaVe5",5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEXX", "SAVE51", "NOTA", "", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000,False,0),
    (999.99,False,60),
    (200,True,30),
    (1500,True,0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class functionality
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.5, 3)
    assert c.items() == { 'apple': (2.5,3) }
    c.add_item('banana',1.0)
    assert c.items()['banana'] == (1.0,1)

def test_cart_remove():
    c = cart.Cart()
    c.add_item('toy',10.0,5)
    c.remove_item('toy',2)
    assert c.items()['toy'][1] == 3
    c.remove_item('toy',3)
    assert 'toy' not in c.items()

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item('item',20.0,4)
    assert c.subtotal() == 80.0

def test_cart_total_no_member_no_coupon():
    c=cart.Cart();c.add_item('x',100,2) # subtotal 200
    assert c.total()==260.0  # 200 + 60 shipping

def test_cart_total_with_member_and_coupon():
    c=cart.Cart();c.add_item('x',200,3)#subtotal600
    total=c.total(member=True,coupon='SAVE10')
    # subtotal 600, coupon 10% ->540, shipping half 30->570
    assert total==570.0

# Test error handling in total
@pytest.mark.parametrize("coupon", ["BADCODE","SAVEX"])
def test_cart_total_invalid_coupon(coupon):
    c=cart.Cart();c.add_item('y',50,1)
    with pytest.raises(ValueError):
        c.total(member=False,coupon=coupon)
