import pytest
import cart

round2=lambda x: round(x,2)

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,expected):
    assert cart.apply_discount(price,percent)==expected

@pytest.mark.parametrize("price,percent",[
    (-1,10),
    (10,-5),
    (10,110)
])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected",[
    (5,0),
    (10,5),
    (55,10),
    (120,15)
])
def test_bulk_discount_percent(quantity,expected):
    assert cart.bulk_discount_percent(quantity)==expected

# parse_coupon tests
@pytest.mark.parametrize("code",["SAVE10","save20","  Save30 "])
def test_parse_coupon_valid(code):
    # expected percent extracted case-insensitively
    import re
    m=re.search(r"\d+", code.strip(), re.IGNORECASE)
    assert cart.parse_coupon(code)==int(m.group(0))

@pytest.mark.parametrize("code",["SAVEX","save0","  SAVE51 ","ABC10"] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected",[
    (1000,False,0.0),
    (999,False,60.0),
    (200,True,30.0),
])
def test_shipping_fee(subtotal,member,expected):
    assert cart.shipping_fee(subtotal, member)==expected

@pytest.mark.parametrize("subtotal",[-10,-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart behavior tests

def test_cart_add_and_items():
    c=cart.Cart()
    assert c.items()=={}
    c.add_item('apple',1.00,2)
    assert c.items()=='{"apple": 2}' or c.items()=={'apple':2}
    c.add_item('apple',1.00,3)
    assert c.items()['apple']==5
    with pytest.raises(ValueError):
        c.add_item('apple',2.00,1)


def test_cart_remove_and_items():
    c=cart.Cart()
    c.add_item('banana',0.50,4)
    c.remove_item('banana',2)
    assert c.items()['banana']==2
    c.remove_item('banana',3)
    assert 'banana' not in c.items()
    with pytest.raises(KeyError):
        c.remove_item('orange',1)


def test_cart_subtotal_and_bulk_discount():
    c=cart.Cart()
    c.add_item('toy',10.00,5)   # no bulk discount -> 50
    c.add_item('balloon',2.00,12) # bulk 5% => 2*12*0.95=22.8
    subtotal=c.subtotal()
    assert subtotal==round2(50+22.8)


def test_cart_total_no_coupon_non_member():
    c=cart.Cart()
    c.add_item('book',200.00,1)
    total=c.total(member=False)
    assert total==round2(260.0)


def test_cart_total_with_coupon_and_member():
    c=cart.Cart()
    c.add_item('pen',5.00,50)  # bulk 10% => 4.5*50=225
    total=c.total(member=True,coupon='SAVE10')
    assert total==round2(232.5)

# Empty cart costs zero and no shipping

def test_cart_empty_total():
    c=cart.Cart()
    assert c.total()==0.0
