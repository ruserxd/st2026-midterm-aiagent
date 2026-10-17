import pytest
import cart
ROUND=lambda x:round(x,2)

# apply_discount
@pytest.mark.parametrize("price,percent,result",[(200,15,170.0),(100,0,100.0),(50,100,0.0)])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==ROUND(result)

@pytest.mark.parametrize("price,percent",[(-1,10),(200,-5),(200,150)])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity,result",[(9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)])
def test_bulk_discount_percent(quantity,result):
    assert cart.bulk_discount_percent(quantity)==result

@pytest.mark.parametrize("qty",[0,-1,3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon
@pytest.mark.parametrize("code,result",[("SAVE10",10),("save20",20),("  SaVe30 ",30)])
def test_parse_coupon_valid(code,result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("code",["","ABC10","SAVE0","SAVE51","SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,result",[(1200,False,0),(1200,True,0),(900,False,60),(900,True,30),(1000,False,0),(999.99,False,60)])
def test_shipping_fee(subtotal,member,result):
    assert cart.shipping_fee(subtotal, member==True)==result

@pytest.mark.parametrize("subtotal",[-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_initial():
    c=cart.Cart()
    assert c.items()=={}
    assert c.subtotal()==0.0
    assert c.total()==0.0


def test_add_and_items():
    c=cart.Cart();c.add_item('apple',10,2)
    assert c.items()['apple']==2

@pytest.mark.parametrize("name,price,q",[("apple",5,1),("banana",3,5)])
def test_add_same_item_price_match(name,price,q):
    c=cart.Cart();c.add_item(name,price);c.add_item(name,price,q-1)
    assert c.items()[name]==q

@pytest.mark.parametrize("name,price,q",[("apple",5,2),("banana",3,4)])
def test_add_same_item_price_mismatch(name,price,q):
    c=cart.Cart()
    c.add_item(name,price)
    with pytest.raises(ValueError):
        c.add_item(name,price+1,q)

@pytest.mark.parametrize("name,quantity",[("apple",0),("banana",-2),("cherry","two")])
def test_add_invalid(name,quantity):
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name,10,quantity)

# Remove item tests

def test_remove_decreases_and_removes():
    c=cart.Cart();c.add_item('apple',5,3);c.remove_item('apple',2)
    assert c.items()['apple']==1
    c.remove_item('apple',1)
    assert 'apple' not in c.items()

def test_remove_nonexistent_raises():
    c=cart.Cart();
    with pytest.raises(KeyError):
        c.remove_item('orange',1)

# Subtotal calculation with bulk discount

def test_subtotal_no_discount():
    c=cart.Cart();c.add_item('item',10,5);assert c.subtotal()==50.0

def test_subtotal_with_bulk_discount():
    c=cart.Cart();c.add_item('item',20,12)
    expected = 20*12*(1-0.05)
    assert ROUND(c.subtotal())==ROUND(expected)

# Total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c=cart.Cart();c.add_item('item',200,5)
    total=c.total(coupon='SAVE10')
    expected = 1000*0.9 + 0
    assert ROUND(total)==ROUND(expected)

# Total empty no shipping

def test_total_empty_no_shipping():
    c=cart.Cart();assert c.total()==0.0
