import pytest
import cart

# ---------- helper assertions for rounding -------

def almost_equal(a,b):
    assert abs(a-b) < 1e-9

# ---------- tests for standalone functions ----------

@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price,percent",[
    (-10,5),(100,-1),(100,101)
])
def test_apply_discount_errors(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

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

@pytest.mark.parametrize("quantity",[-1,0,3.5,'a'])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code,result",[
    ('SAVE10',10),('save20',20),('  Save30 ',30),('sAvE5',5),('SAVE50',50)
])
def test_parse_coupon_valid(code,result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("code",["SAVE0","SAVE51","ABCD10","save-5","",None,123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping fee tests ----------

@pytest.mark.parametrize("subtotal,member,result",[
    (0,False,60),
    (999.99,True,30),
    (1000,False,0),
])
def test_shipping_fee(subtotal,member,result):
    assert cart.shipping_fee(subtotal, member)==result

@pytest.mark.parametrize("subtotal",[-10,-1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initial_empty():
    c=cart.Cart()
    assert c.items()=={}
    assert c.subtotal()==0
    assert c.total()==0

# Adding items, price match enforcement

def test_add_item_and_subtotal():
    c=cart.Cart()
    c.add_item('apple', 1.00, 10)
    # bulk discount of 5% for 10 units -> total 10*1 -5% =9.5
    assert almost_equal(c.subtotal(),9.5)
    c.add_item('banana',0.50,2)
    assert almost_equal(c.subtotal(),9.5+1.00) # 2*0.5=1 with no bulk discount

def test_add_same_item_increases_quantity_and_price_match():
    c=cart.Cart()
    c.add_item('apple',2.0,3)
    c.add_item('apple',2.0,2)
    assert c.items()['apple']==5
    # price must match, else error
    with pytest.raises(ValueError):
        c.add_item('apple',3.0,1)

# Removing items and bug detection

def test_remove_item_and_bug():
    c=cart.Cart()
    c.add_item('cherry',0.2,5)
    # remove 3 -> should leave 2
    c.remove_item('cherry',3)
    assert c.items()['cherry']==2
    # removing more than existing: currently bug deletes only if <0; should raise or remove all
    with pytest.raises(KeyError):
        # removal of non-existing item
        c.remove_item('pineapple')
    # removing 5 from remaining 2 should remove the item entirely (expected behaviour)
    c.remove_item('cherry',5)
    assert 'cherry' not in c.items()

# Coupon application and shipping calculation bug detection

def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('widget',100,2)  # subtotal 200 with no bulk discount
    # apply coupon SAVE10 => 180
    total = c.total(coupon='SAVE10')
    # shipping on amount after coupon: 180 >= 1000? no -> 60
    assert almost_equal(total,240.0)

# test that member flag does not affect shipping in buggy implementation

def test_member_shipping_bug():
    c=cart.Cart()
    c.add_item('gadget',2000,1)  # subtotal >1000
    # shipping should be free regardless of member flag but code uses subtotal before coupon
    total_non_member = c.total(member=False)
    total_member = c.total(member=True)
    assert total_non_member==total_member

# test that empty cart has no shipping

def test_empty_cart_no_shipping():
    c=cart.Cart()
    assert c.total()==0
