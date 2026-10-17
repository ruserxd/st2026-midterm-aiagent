import pytest
import cart

def approx(a,b,tol=1e-2):
    return abs(a-b)<=tol

# apply_discount tests
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price",[-1,-0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price,10)

@pytest.mark.parametrize("percent",[-5,105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100,percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected",[
    (9,0),(10,5),(49,5),(50,10),(99,10),(100,15),
])
def test_bulk_discount(qty,expected):
    assert cart.bulk_discount_percent(qty)==expected

@pytest.mark.parametrize("qty",[0,-5,2.3])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty)) if isinstance(qty,int) else cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected",[
    ('SAVE10',10),('save10','10'),(' SAVE20 ','20'),('SaVe30','30')
])
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code)==int(expected)

@pytest.mark.parametrize("code",['save0','savexx','SAVE51','NOPE',''])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,result",[
    (1001,False,0),(999.99,False,60),(0,True,30),(500,True,30),
])
def test_shipping(subtotal,member,result):
    assert cart.shipping_fee(subtotal, member)==result

# Cart tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_subtotal(empty_cart):
    assert empty_cart.subtotal()==0.0

def test_add_item(empty_cart):
    empty_cart.add_item('apple',100,2)
    assert empty_cart.items()=='{'+'"apple": 2'+'}'
    empty_cart.add_item('apple',100,3)
    assert empty_cart.items()=='{'+'"apple": 5'+'}'


def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item('banana',50,1)
    with pytest.raises(ValueError):
        empty_cart.add_item('banana',60,1)


def test_remove_item(empty_cart):
    empty_cart.add_item('orange',30,5)
    empty_cart.remove_item('orange',2)
    assert empty_cart.items()=='{'+'"orange": 3'+'}'
    empty_cart.remove_item('orange',3)
    assert empty_cart.items()=={}


def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item('kiwi',1)


def test_subtotal_with_bulk():
    c=cart.Cart()
    c.add_item('itemA',100,10)  # 5% discount per unit
    assert approx(c.subtotal(),950.0)


def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('pen',200,1)
    c.add_item('pencil',50,3)
    total=c.total(member=False,coupon='SAVE10')
    assert approx(total,375.0)


def test_total_empty():
    c=cart.Cart()
    assert c.total()==0.0
