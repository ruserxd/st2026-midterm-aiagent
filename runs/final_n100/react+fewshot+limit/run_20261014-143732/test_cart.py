import pytest
import cart

# ----- Basic function tests -----
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0)
])
def test_apply_discount_valid(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price,percent",[
    (-1,10),(50,-5),(50,105)
])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# ----- Bulk discount tests -----
@pytest.mark.parametrize("qty,expected",[
    (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount(qty,expected):
    assert cart.bulk_discount_percent(qty)==expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)  # non positive

# ----- Coupon parsing tests -----
@pytest.mark.parametrize("code,expected",[
    ("SAVE10",10), ("save20",20), (" SAVE30 ",30)
])
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code)==expected

with pytest.raises(ValueError):
    cart.parse_coupon("SAVEX")
with pytest.raises(ValueError):
    cart.parse_coupon("SAVE0")
with pytest.raises(ValueError):
    cart.parse_coupon("SAVE51")

# ----- Shipping fee tests -----
@pytest.mark.parametrize("subtotal,member,fee",[
    (1000,False,0.0),(1500,True,0.0),(999,False,60.0),(800,True,30.0)
])
def test_shipping(subtotal,member,fee):
    assert cart.shipping_fee(subtotal,member)==fee

with pytest.raises(ValueError):
    cart.shipping_fee(-1)

# ----- Cart class tests -----
@pytest.fixture
def empty_cart():
    return cart.Cart()

# Add item tests

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0,2)
    assert empty_cart.items()=={"apple":2}

def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana",0.5,3)
    empty_cart.add_item("banana",0.5,2)
    assert empty_cart.items()=={"banana":5}

# Validation on add_item

def test_add_item_invalid_unit_price():
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("x",-1,1)

def test_add_item_invalid_quantity():
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("y",1,-1)

def test_add_item_price_mismatch():
    c=cart.Cart()
    c.add_item("z",2,1)
    with pytest.raises(ValueError):
        c.add_item("z",3,1)  # price diff

# Remove item tests

def test_remove_partial_and_full(empty_cart):
    empty_cart.add_item("cherry",0.2,5)
    empty_cart.remove_item("cherry",3)
    assert empty_cart.items()=={"cherry":2}
    empty_cart.remove_item("cherry",2)
    assert empty_cart.items() == {}

def test_remove_nonexistent():
    with pytest.raises(KeyError):
        cart.Cart().remove_item("nope",1)

# Subtotal tests

def test_subtotal_no_discount(empty_cart):
    c=empty_cart
    c.add_item("item",10,9)
    assert c.subtotal()==90.0  # no discount

def test_subtotal_with_bulk_discount():
    c=cart.Cart()
    c.add_item("item",10,10)
    assert c.subtotal()==95.0  # 5% off 100

# Multiple items subtotal

def test_multiple_items_subtotal():
    c=cart.Cart()
    c.add_item("a",2,50)   # 100 -10% =90
    c.add_item("b",3,60)   # 180 -10% =162
    assert c.subtotal()==252.0

# Total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item("s1",20,5)   # subtotal 100
    total=c.total(member=False,coupon="SAVE10")
    # after 10%:90; shipping 60 =>150
    assert total==150.0

# Member half shipping

def test_total_member_half_shipping():
    c=cart.Cart()
    c.add_item("s2",200,1)   # subtotal 200
    # member pays half shipping => 30
    assert c.total(member=True)==230.0

# Free shipping over 1000

def test_total_free_shipping_over_1000():
    c=cart.Cart()
    c.add_item("big",1200,1)
    assert c.total()==1200.0

# Empty cart total

def test_empty_cart_total_zero():
    empty=cart.Cart()
    assert empty.total()==0.0
