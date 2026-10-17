import pytest
import cart

# ---------- Utility for rounding comparisons ------------

def round2(x):
    return round(float(x),2)

# ---------- apply_discount tests ------------------------
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0)
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price",[-1,-0.01])
def def_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price,10)

@pytest.mark.parametrize("percent",[-5,105])
def test_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100,percent)

# ---------- bulk_discount_percent tests -----------------
@pytest.mark.parametrize("qty,expected",[
    (9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)
])
def test_bulk_discount_percent(qty,expected):
    assert cart.bulk_discount_percent(qty)==expected

@pytest.mark.parametrize("qty",[0,-5,3.2])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests --------------------------
@pytest.mark.parametrize("code,exp",[
    ('SAVE10',10),('save20',20),(' SAVE30 ',30)
])
def test_parse_coupon_valid(code,exp):
    assert cart.parse_coupon(code)==exp

@pytest.mark.parametrize("code",['','INVALID','SAVE0','SAVE51','SAVExx'])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests --------------------------
@pytest.mark.parametrize("subtotal,member,fee",[
    (999,False,60),(1000,False,0),(1500,False,0),(500,True,30),(500,False,60)
])
def test_shipping_fee(subtotal,member,fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal",[-10,-1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality tests --------------------
class DummyCart:
    def __init__(self):
        self.c=cart.Cart()

@pytest.fixture
def c():
    return cart.Cart()

def test_add_item_and_items(c):
    c.add_item('apple',1.0,2)
    assert c.items()=={'apple':2}
    c.add_item('apple',1.0,3)
    assert c.items()['apple']==5
    with pytest.raises(ValueError):
        c.add_item('apple',1.5,1)

def test_remove_item(c):
    c.add_item('banana',2.0,5)
    c.remove_item('banana',3)
    assert c.items()['banana']==2
    c.remove_item('banana',2)
    assert 'banana' not in c.items()
    with pytest.raises(KeyError):
        c.remove_item('banana',1)

def test_subtotal_with_bulk(c):
    c.add_item('itemA',10.0,9)  # no discount
    c.add_item('itemB',5.0,10)  # 5% discount
    expected = round2(10.0*9 + 5.0*10*(1-0.05))
    assert round2(c.subtotal()) == expected

def test_total_with_coupon_and_shipping(c):
    c.add_item('widget',200,6)  # no bulk discount
    amount_after_coupon = cart.apply_discount(c.subtotal(),20)
    expected = round2(amount_after_coupon + cart.shipping_fee(amount_after_coupon))
    assert round2(c.total(coupon='SAVE20')) == expected

    with pytest.raises(ValueError):
        c.total(coupon='BADCODE')

def test_total_member_shipping(c):
    c.add_item('gadget',500,1)
    expected = round2(500 + cart.shipping_fee(500, member=True))
    assert round2(c.total(member=True)) == expected

def test_empty_cart_cost_zero(c):
    assert c.total()==0
