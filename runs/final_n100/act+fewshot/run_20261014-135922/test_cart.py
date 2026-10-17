import pytest
import cart

# apply_discount spec tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,result", [
    (9, 0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(qty,result):
    assert cart.bulk_discount_percent(qty)==result

@pytest.mark.parametrize("qty", [0,-1,5.5,'a'])
def test_bulk_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,result", [
    ('SAVE10',10),('save25','25'),('  SAVE50  ','50')])
def test_parse_coupon_valid(code,result):
    assert cart.parse_coupon(code)==int(result)

@pytest.mark.parametrize("code", ['sav10','SAVE0','SAVE51','ABC',''])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,result", [
    (0,False,60),
    (999.99,True,30),
    (1000,False,0),
])
def test_shipping_fee(subtotal,member,result):
    assert cart.shipping_fee(subtotal, member)==result

# Cart tests
def test_cart_add_and_subtotal():
    c=cart.Cart()
    c.add_item('apple',2.5,4)
    c.add_item('banana',1.0,6)
    assert c.items() == {'apple':4,'banana':6}
    # subtotal: apple 10 + banana 6 = 16
    assert c.subtotal()==16.0

# test bulk discount effect
c=cart.Cart()
c.add_item('item',10,12)  # qty>=10 ->5% discount
assert c.subtotal()==120*0.95==114.0

# total with coupon and shipping
c=cart.Cart();c.add_item('x',100,1)
# subtotal 100; apply coupon SAVE10 ->90; shipping 60 -> total150
assert c.total(coupon='SAVE10')==150.0
# member discount shipping half
assert c.total(member=True,coupon='SAVE10')==120.0

# test invalid removal and negative quantity
c=cart.Cart();c.add_item('y',5,2)
with pytest.raises(KeyError):
    c.remove_item('z')
# remove more than present -> item removed entirely
c.remove_item('y',3)
assert 'y' not in c.items()
