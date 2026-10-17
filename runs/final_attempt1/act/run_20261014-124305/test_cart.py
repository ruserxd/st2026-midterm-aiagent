import pytest
from cart import *

# test apply_discount
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert apply_discount(price,percent)==result

# invalid values
@pytest.mark.parametrize("price,percent",[( -1,10),(200,-5),(200,120)])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        apply_discount(price,percent)

# bulk discount percent
@pytest.mark.parametrize("q,exp",[(5,0),(9,0),(10,5),(50,10),(100,15),(200,15)])
def test_bulk_discount(q,exp):
    assert bulk_discount_percent(q)==exp

with pytest.raises(ValueError):
    bulk_discount_percent(0)

# parse coupon
@pytest.mark.parametrize("code,exp",[('SAVE10',10),('save20',20),('  SaVe30  ',30)])
def test_parse_coupon_valid(code,exp):
    assert parse_coupon(code)==exp

with pytest.raises(ValueError):
    parse_coupon('SAVEX')

# shipping fee
@pytest.mark.parametrize("subtotal,member,exp",[(0.01,False,60),(1000,False,0),(999,True,30)])
def test_shipping(subtotal,member,exp):
    assert shipping_fee(subtotal,member)==exp

with pytest.raises(ValueError):
    shipping_fee(-5)

# Cart behavior
@pytest.mark.parametrize("items",[
    [],
    [('apple',1.0,2),('banana',2.0,3)],
])
def test_cart_subtotal(items):
    cart=Cart()
    for n,p,q in items:
        cart.add_item(n,p,q)
    expected=sum(p*q for _,p,q in items)
    assert cart.subtotal()==expected

# total with coupon and shipping rounding
cart=Cart()
cart.add_item('item',100,1)  # subtotal 100
assert cart.total(member=False,coupon='SAVE10')==round(90+60,2)
assert cart.total(member=True,coupon='save20')==round(80+30,2)
# no coupon shipping free after $1000
cart=Cart()
for i in range(11):
    cart.add_item(f'item{i}',100,i+1)  # subtotal >1100
assert cart.total(member=False)==round(cart.subtotal()+0,2)
