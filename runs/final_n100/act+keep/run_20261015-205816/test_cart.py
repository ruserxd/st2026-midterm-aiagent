import pytest
from cart import apply_discount,bulk_discount_percent,parse_coupon,shipping_fee,Cart

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0)
])
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent)==result

# error conditions
@pytest.mark.parametrize("price",[-1, -5])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent",[-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,disc",[(1,0),(4,5),(10,10)])
def test_bulk_discount_percent(qty, disc):
    assert bulk_discount_percent(qty)==disc

# parse_coupon: doc says returns dict with keys 'type','value'
@pytest.mark.parametrize("code,result",[
    ('SAVE10',{'type':'fixed','value':10}),
    ('OFF20',{'type':'percent','value':20})
])
def test_parse_coupon(code,result):
    assert parse_coupon(code)==result

# shipping_fee
@pytest.mark.parametrize("subtotal,member,fee",[(50,False,5),(150,True,0)])
def test_shipping_fee(subtotal, member, fee):
    assert shipping_fee(subtotal, member==True)==fee

# Cart tests
@pytest.fixture
def cart():
    return Cart()

def test_add_and_items(cart):
    cart.add_item('apple',2.5)
    assert cart.items() == [{'name':'apple','unit_price':2.5,'quantity':1}]

def test_subtotal(cart):
    cart.add_item('apple',3,2)
    assert cart.subtotal()==6

def test_total_with_coupon_and_member(cart):
    cart.add_item('book',20,1)
    coupon=parse_coupon('SAVE10')
    total=cart.total(member=True,coupon=coupon)
    # subtotal 20, member shipping 0, coupon fixed 10 -> final 10
    assert total==10
