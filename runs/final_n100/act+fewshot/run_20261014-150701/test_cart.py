import pytest
import cart

def d(x): return round(x,2)

@pytest.mark.parametrize("price,percent,expected",[
    (200,15,170.0),
    (100,50,50.0),
    (123.45,10,111.11),
])
def test_apply_discount(price,percent,expected):
    assert cart.apply_discount(price,percent)==expected

@pytest.mark.parametrize("subtotal,expected",[
    (0,60),(999,60),(1000,0),(1500,0)
])
def test_shipping_fee(subtotal,expected):
    assert cart.shipping_fee(subtotal)==expected
    if subtotal<1000:
        assert cart.shipping_fee(subtotal,member=True)==expected/2
    else:
        assert cart.shipping_fee(subtotal,member=True)==0

@pytest.mark.parametrize("code",["SAVE10","save20","  Save30  "])
def test_parse_coupon_valid(code):
    import re
    m=re.search(r'SAVE(\d+)',code.strip(),re.I)
    n=int(m.group(1))
    assert cart.parse_coupon(code)==n

@pytest.mark.parametrize("code",["SAVE0","SAVE51","NOTACODE","SAVEX10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_add_and_items():
    c=cart.Cart()
    c.add_item('apple',0.5,2)
    c.add_item('banana',1.0,3)
    assert c.items()=={'apple':2,'banana':3}
    c.add_item('apple',0.5,1)
    assert c.items()['apple']==3


def test_add_invalid():
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('apple',-1,1)
    with pytest.raises(ValueError):
        c.add_item('orange',0.5,0)


def test_remove_and_items():
    c=cart.Cart()
    c.add_item('apple',0.5,3)
    c.remove_item('apple',2)
    assert c.items()['apple']==1
    c.remove_item('apple',1)
    assert 'apple' not in c.items()


def test_remove_invalid():
    c=cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('pear',1)


def test_subtotal_bulk_discount():
    c=cart.Cart()
    c.add_item('widget',10.0,5)
    assert d(c.subtotal())==50.00
    c.remove_item('widget',3) # qty=2
    assert d(c.subtotal())==20.00


def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('item',100,1)
    total=c.total(member=False,coupon='SAVE10')
    assert d(total)==150.00
    total_member=c.total(member=True,coupon='SAVE20')
    assert d(total_member)==110.00


def test_total_empty_cart():
    c=cart.Cart()
    assert c.total()==0
