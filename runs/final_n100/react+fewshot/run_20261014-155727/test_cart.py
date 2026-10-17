import pytest
import cart

# Helper to assert rounding with two decimals

def approx_two(x, y):
    return round(x,2)==round(y,2)

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==result

# Error cases
@pytest.mark.parametrize("price,percent", [(-1,10),(10,-5),(10,105)])
def test_apply_discount_errors(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# bulk discount percent
@pytest.mark.parametrize("quantity,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(quantity,expected):
    assert cart.bulk_discount_percent(quantity)==expected

# error for non positive integer
@pytest.mark.parametrize("quantity", [0,-5,3.2,"a"])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse coupon
valids=[("SAVE10",10),("save20",20),("  SaVe30 ",30)]
@pytest.mark.parametrize("code,expected", valids)
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code)==expected

invalids=["INVALID","SAVExx","SAVE0","SAVE51","",None]
@pytest.mark.parametrize("code", invalids)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (999,False,60),
    (1000,False,0),
    (1500,True,30),
    (500,True,30),
])
def test_shipping_fee(subtotal,member,expected):
    assert cart.shipping_fee(subtotal,member==True)==expected

# shipping fee errors
@pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_initial_empty():
    c=cart.Cart()
    assert c.items()=={}
    assert c.subtotal()==0.0
    assert c.total()==0.0


def test_add_item_and_subtotal():
    c=cart.Cart()
    c.add_item('apple',1.00,3)
    c.add_item('banana',2.50,2)
    # apple subtotal: 1*3=3, no bulk discount (<10)
    # banana subtotal: 2.5*2=5, no bulk
    assert approx_two(c.subtotal(),8.0)


def test_add_existing_item_increases_quantity_and_price_check():
    c=cart.Cart()
    c.add_item('apple',1.00,3)
    with pytest.raises(ValueError):
        c.add_item('apple',1.50,2)  # price mismatch
    c.add_item('apple',1.00,2)
    assert c.items()['apple']==5


def test_remove_item():
    c=cart.Cart()
    c.add_item('orange',0.75,4)
    c.remove_item('orange',2)
    assert c.items()['orange']==2
    c.remove_item('orange',2)
    assert 'orange' not in c.items()
    with pytest.raises(KeyError):
        c.remove_item('pear',1)


def test_bulk_discount_in_subtotal():
    c=cart.Cart()
    # 12 apples: bulk discount 5%
    c.add_item('apple',2.00,12)  # base 24 -> 24*0.95=22.8
    assert approx_two(c.subtotal(),22.80)


def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('widget',100.00,5)  # subtotal 500, no bulk discount (qty<10)
    amount=c.total(coupon='SAVE10')   # apply 10% coupon -> 450
    assert approx_two(amount,450.0)
    # shipping on 450: member? default False => 60
    amount_with_ship=c.total(coupon='SAVE10',member=True)  # half shipping 30
    assert approx_two(amount_with_ship,480.0)


def test_total_empty_cart_no_shipping():
    c=cart.Cart()
    assert c.total()==0.0
