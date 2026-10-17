import pytest
import cart

# Helper: round to 2 decimals using apply_discount etc.

def approx(value, expected):
    assert abs(value - expected) < 0.005

# Test apply_discount
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Errors in apply_discount
@pytest.mark.parametrize("price",[-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent",[-5,105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,exp",[(1,0),(9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)])
def test_bulk_discount_percent(qty, exp):
    assert cart.bulk_discount_percent(qty) == exp

@pytest.mark.parametrize("qty",[0,-1])
def test_bulk_discount_negative(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon
@pytest.mark.parametrize("code,exp",[
    ("SAVE10",10),
    ("save20 ",20),
    ("  SaVe50  ",50),
])
def test_parse_coupon_valid(code, exp):
    assert cart.parse_coupon(code) == exp

@pytest.mark.parametrize("code",["SAVE0","SAVE51","NOTVALID","SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,exp",[
    (1200,False,0),
    (999.99,False,60),
    (0,True,30),
])
def test_shipping_fee(subtotal, member, exp):
    assert cart.shipping_fee(subtotal, member) == exp

@pytest.mark.parametrize("subtotal",[-1,-100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.5, 3)
    c.add_item('banana', 1.0, 5)
    assert c.items() == {'apple':3,'banana':5}

def test_cart_add_existing_same_price():
    c=cart.Cart()
    c.add_item('toy',10,2)
    c.add_item('toy',10,1)
    assert c.items()=={'toy':3}

def test_cart_add_existing_different_price_raises():
    c=cart.Cart()
    c.add_item('book',15,1)
    with pytest.raises(ValueError):
        c.add_item('book',12,2)

# subtotal calculation
@pytest.mark.parametrize("items,total",[
    ({'a':(10,1)},10.0),
    ({'b':(5,10)},47.5), # bulk 5% off: 50-2.5=47.5
])
def test_subtotal(items,total):
    c=cart.Cart()
    for name,(price,qty) in items.items():
        c.add_item(name, price, qty)
    assert round(c.subtotal(),2)==round(total,2)

# total with coupon and shipping
def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('pen',5,100) # bulk 15%: 500-75=425
    amount = round(c.subtotal(),2) # subtotal already discounted by bulk
    # no coupon
    total_no_coupon = round(amount + cart.shipping_fee(amount),2)
    assert round(c.total(),2)==total_no_coupon
    # with valid coupon SAVE10 - 10%
    discounted = cart.apply_discount(amount,10)
    total_with_coup = round(discounted + cart.shipping_fee(discounted),2)
    assert round(c.total(coupon='SAVE10'),2)==total_with_coup

# empty cart
def test_empty_cart_total():
    c=cart.Cart()
    assert c.subtotal()==0
    assert c.total()==0

# coupon invalid raises
def test_invalid_coupon_raises():
    c=cart.Cart()
    c.add_item('x',1,1)
    with pytest.raises(ValueError):
        c.total(coupon='BADCODE')

# remove_item tests
def test_remove_item_reduce_only():
    c=cart.Cart()
    c.add_item('g',3,4)
    c.remove_item('g',2)
    assert c.items() == {'g':2}

def test_remove_item_zero_or_less_removes():
    c=cart.Cart()
    c.add_item('h',2,3)
    c.remove_item('h',5)  # removes item
    assert 'h' not in c.items()

def test_remove_nonexistent_raises():
    c=cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('notpresent',1)
