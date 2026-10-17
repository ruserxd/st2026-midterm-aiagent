import pytest
import cart

# Helper: assert raise
def _assert_raises(exc, func, *args, **kwargs):
    with pytest.raises(exc):
        func(*args,**kwargs)

######################
# apply_discount tests
######################
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==result

def test_apply_discount_errors():
    _assert_raises(ValueError,cart.apply_discount,-10,20)
    _assert_raises(ValueError,cart.apply_discount,100,120)

######################
# bulk_discount_percent tests
######################
@pytest.mark.parametrize("qty,exp",[(5,0),(10,5),(49,5),(50,10),(99,10),(100,15)])
def test_bulk_discount(qty,exp):
    assert cart.bulk_discount_percent(qty)==exp

def test_bulk_discount_error():
    _assert_raises(ValueError,cart.bulk_discount_percent,-1)

######################
# parse_coupon tests
######################
@pytest.mark.parametrize("code,result",[("SAVE10",10),("save20",20),("  SaVe5 ",5)])
def test_parse_coupon(code,result):
    assert cart.parse_coupon(code)==result

def test_parse_coupon_error():
    _assert_raises(ValueError,cart.parse_coupon,"INVALID")

######################
# shipping_fee tests
######################
@pytest.mark.parametrize("subtotal,member,result",[(0.01,False,60),(1000,False,0),(999,True,30)])
def test_shipping(subtotal,member,result):
    assert cart.shipping_fee(subtotal,member)==result

def test_shipping_error():
    _assert_raises(ValueError,cart.shipping_fee,-1)

######################
# Cart class tests
######################
def test_cart_add_and_items():
    c=cart.Cart()
    c.add_item('apple',1.0,2)
    c.add_item('banana',0.5)
    assert c.items()=={'apple':2,'banana':1}
    # adding existing increases qty
    c.add_item('apple',1.0,3)
    assert c.items()['apple']==5

    # price mismatch raises
    with pytest.raises(ValueError):
        c2=cart.Cart();c2.add_item('x',2.0);c2.add_item('x',3.0)

    # remove item
    c.remove_item('apple',3)  # remaining 2
    assert c.items()['apple']==2
    c.remove_item('apple',2)  # should be removed completely
    assert 'apple' not in c.items()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

    # subtotal with bulk discount
    c.add_item('item',10,100)
    # bulk 15% -> 850.00
    assert c.subtotal()==850.0

    # total calculation
    # subtotal 850, coupon 10% -> 765, shipping 60 (non-member) -> 825
    assert c.total(coupon='SAVE10')==825.0
    # member shipping half
    assert c.total(member=True,coupon='SAVE10')==795.0
    # empty cart cost 0
    d=cart.Cart()
    assert d.total()==0.0
