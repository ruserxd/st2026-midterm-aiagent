import pytest
import cart

ROUND=lambda x: round(x,2)

# ----------------- basic helpers ---------------------------------
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==ROUND(result)

# invalid price or percent
@pytest.mark.parametrize("price,percent",[
    (-1,10),
    (100,-5),
    (100,105),
])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

@pytest.mark.parametrize("quantity,expected",[
    (9,0),(10,5),(49,5),(50,10),(99,10),(100,15),])
def test_bulk_discount_percent(quantity,expected):
    assert cart.bulk_discount_percent(quantity)==expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)

@pytest.mark.parametrize("code,result",[
    ('SAVE10',10),('save20',20),('  SaVe30  ',30),])
def test_parse_coupon_valid(code,result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("invalid_code",['SAVEX','SAVE51','  BAD10'])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

@pytest.mark.parametrize("subtotal,member,result",[
    (0,False,60),(999.99,True,30),(1000,False,0),])
def test_shipping_fee(subtotal,member,result):
    assert cart.shipping_fee(subtotal,member)==result

with pytest.raises(ValueError):
    cart.shipping_fee(-5)

# ----------------- Cart class tests ---------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item

def test_add_new_item(empty_cart):
    empty_cart.add_item('apple',1.0,3)
    assert empty_cart.items()=={'apple':3}

def test_add_existing_same_price(empty_cart):
    empty_cart.add_item('banana',2.5,2)
    empty_cart.add_item('banana',2.5,1)
    assert empty_cart.items()['banana']==3

def test_add_existing_diff_price_raises():
    c=cart.Cart()
    c.add_item('cherry',0.5,1)
    with pytest.raises(ValueError):
        c.add_item('cherry',0.6,1)

# remove_item

def test_remove_decrement(empty_cart):
    empty_cart.add_item('durian',3.0,4)
    empty_cart.remove_item('durian',2)
    assert empty_cart.items()['durian']==2

def test_remove_zero_removes(empty_cart):
    empty_cart.add_item('egg',1.0,2)
    empty_cart.remove_item('egg',2)
    assert 'egg' not in empty_cart.items()

def test_remove_nonexistent_raises(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item('fig',1)

# subtotal
@pytest.mark.parametrize("items,expected",[
    ({"a":(10.0,9)},90.0),
    ({"b":(20.0,10)},180.0),
    ({"c":(30.0,50)},1350.0),
    ({"d":(40.0,100)},3400.0),])
def test_subtotal(items,expected):
    c=cart.Cart()
    for name,(price,q) in items.items():
        c.add_item(name,price,q)
    assert ROUND(c.subtotal())==ROUND(expected)

# total with coupon and shipping

def test_total_full(empty_cart):
    empty_cart.add_item('item',100.0,1)
    # subtotal 100 (no bulk discount)
    assert empty_cart.total()==160.0   # 100 + 60 shipping
    assert empty_cart.total(member=True)==130.0
    assert empty_cart.total(coupon='SAVE10')==150.0
    assert empty_cart.total(member=True,coupon='SAVE20')==140.0

# empty cart
empty=cart.Cart()
assert empty.subtotal()==0
assert empty.total()==0
