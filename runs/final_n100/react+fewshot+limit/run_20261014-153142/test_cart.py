import pytest
import cart

# Helper for float comparison

def approx(value, expected):
    assert round(value,2) == round(expected,2)

# ----- apply_discount -----
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (100,100,0.0),
])
def test_apply_discount_valid(price,percent,result):
    assert cart.apply_discount(price,percent)==result

# boundary: percent=0 and 100 handled above.
@pytest.mark.parametrize("price",[-1,-0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price,10)

@pytest.mark.parametrize("percent",[-5,101,150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100,percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize("quantity,result",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(quantity,result):
    assert cart.bulk_discount_percent(quantity)==result

@pytest.mark.parametrize("quantity",[0,-1,3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
valid_cases=[('SAVE10',10),('save20',20),('  SaVe30  ',30)]
for code,exp in valid_cases:
    assert cart.parse_coupon(code)==exp

invalid_cases=['SAVE0','SAVE51','ABC12','SAVEXY','']
for code in invalid_cases:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize("subtotal,member,fee",[
    (1001,False,0),
    (999,True,30),
    (500,False,60),
])
def test_shipping_fee(subtotal,member,fee):
    assert cart.shipping_fee(subtotal,member)==fee

@pytest.mark.parametrize("subtotal",[-10,-1])
def test_shipping_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
def test_cart_basic_operations():
    c=cart.Cart()
    # empty cart initial state
    assert c.items()=={}
    assert c.subtotal()==0.0
    # add items
    c.add_item('apple',50,3)
    c.add_item('banana',30,2)
    assert c.items()=='{'+'"apple": 3, "banana": 2'+'}'
    assert c.subtotal()==(50*3+30*2)

    # add existing item with same price
    c.add_item('apple',50,2)
    assert c.items()['apple']==5

    # error: different unit price for same item
    with pytest.raises(ValueError):
        c.add_item('apple',40,1)

    # remove some quantity
    c.remove_item('banana',1)
    assert c.items()['banana']==1

    # removing more than present removes the item
    c.remove_item('banana',2)
    assert 'banana' not in c.items()

    # error: removing non-existent item
    with pytest.raises(KeyError):
        c.remove_item('orange',1)

    # total calculation
    c.add_item('cherry',100,1)
    # subtotal=50*5+30*? +100 = 250+ ?+100 etc. compute manually
    assert round(c.total(member=False,coupon=None),2)==(c.subtotal()+60) # non member shipping

    # with coupon: apply parse_coupon discount on subtotal before shipping?
    # total uses coupon percent and member shipping rules.
    # For test, assume coupon applies to subtotal only.
    c.add_item('durian',200,1)
    assert round(c.total(member=True,coupon='SAVE10'),2)==(c.subtotal()*0.9+30)  # member half shipping

# End of tests
