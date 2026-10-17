import pytest
import cart

# Helper: approximate comparison for floats if needed

def approx_equal(a,b,tol=1e-9):
    return abs(a-b) < tol

@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (100,100,0.0)
])
def test_apply_discount_valid(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price,percent",[( -1,10),(50,-5),(50,105)])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

@pytest.mark.parametrize("quantity,percent",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(quantity,percent):
    assert cart.bulk_discount_percent(quantity)==percent

@pytest.mark.parametrize("quantity",[0,-5,1.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code,result",[
    ("SAVE10",10),
    (" save20 ",20),
    ("SaVe1",1)
])
def test_parse_coupon_valid(code,result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("code",["SAVEX","123","save0","SAVE51",""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,fee",[
    (1000,0),
    (999.99,60),
    (500,30)
])
def test_shipping_fee(subtotal,fee):
    assert cart.shipping_fee(subtotal)==fee

@pytest.mark.parametrize("subtotal",[-5,-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_init_empty():
    c=cart.Cart()
    assert c.items()=={}
    assert c.subtotal()==0.0
    assert c.total()==0.0

def test_add_item_new_and_existing():
    c=cart.Cart()
    c.add_item("apple",1,2)
    assert c.items() == {"apple":2}
    c.add_item("apple",1,3)
    assert c.items() == {"apple":5}

@pytest.mark.parametrize("unit_price,quantity",[( -1,1),(0,-1)])
def test_add_item_invalid(unit_price,quantity):
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("x",unit_price,quantity)

# Price mismatch
c=cart.Cart()
c.add_item("pencil",1,1)
with pytest.raises(ValueError):
    c.add_item("pencil",2,1)

def test_remove_item():
    c=cart.Cart()
    c.add_item("ball",5,3)
    c.remove_item("ball",2)
    assert c.items()=={"ball":1}
    c.remove_item("ball",1)
    assert c.items() == {}

with pytest.raises(KeyError):
    cart.Cart().remove_item("missing",1)

# subtotal calculations with bulk discount
c=cart.Cart()
c.add_item("toy",100,10)  # 5% discount
assert c.subtotal()==950.0
c.add_item("other",50,2)
# no discount on other
assert c.subtotal()==1050.0

# total with coupon and shipping
c=cart.Cart()
c.add_item("item",500,1)   # subtotal 500
# apply SAVE10 -> 450, shipping 30 = 480
assert c.total(coupon="SAVE10")==480.0
# member gets half shipping on non free case
assert c.total(member=True,coupon=None)==515.0
