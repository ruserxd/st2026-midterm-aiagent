import pytest
import cart

# Helper for rounding issues
@pytest.mark.parametrize("price,percent,expected", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,expected):
    assert cart.apply_discount(price,percent)==expected

@pytest.mark.parametrize("quantity,expected",[
    (5,0),
    (10,5),
    (50,10),
    (100,15)
])
def test_bulk_discount_percent(quantity,expected):
    assert cart.bulk_discount_percent(quantity)==expected

@pytest.mark.parametrize("code,expected",[
    ('SAVE10',10),
    (' save20 ',20),
    ('SaVe5',5),
])
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code)==expected

@pytest.mark.parametrize("code",['INVALID','SAVEXY','save0','save51'])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected_fee",[
    (0,False,60),
    (500,True,30),
    (1000,False,0),
])
def test_shipping_fee(subtotal,member,expected_fee):
    assert cart.shipping_fee(subtotal,member)==expected_fee

# Cart functionality tests
@pytest.mark.parametrize("name,price,quantity",[
    ('apple',1.00,2),
    ('banana',0.50,5)
])
def test_add_item(name,price,quantity):
    c=cart.Cart()
    c.add_item(name,price,quantity)
    assert c.items()=={name:quantity}

# Duplicate add increases quantity

def test_add_duplicate_increases_quantity():
    c=cart.Cart()
    c.add_item('apple',1.0,2)
    c.add_item('apple',1.0,3)
    assert c.items()['apple']==5

# Adding with different price raises

def test_add_different_price_raises():
    c=cart.Cart()
    c.add_item('apple',1.0,1)
    with pytest.raises(ValueError):
        c.add_item('apple',2.0,1)

# Remove item reduces quantity and removes when zero

def test_remove_item_reduces_and_removes():
    c=cart.Cart()
    c.add_item('orange',0.8,4)
    c.remove_item('orange',2)
    assert c.items()['orange']==2
    c.remove_item('orange',2)
    assert 'orange' not in c.items()

# Removing non-existent item raises KeyError

def test_remove_nonexistent_raises():
    c=cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('pear',1)

# Subtotal calculations with bulk discount

def test_subtotal_with_bulk_discount():
    c=cart.Cart()
    # 10 apples at $2 each => bulk discount 5%
    c.add_item('apple',2.0,10)
    expected = 2.0*10*(1-0.05)  # 19.0
    assert round(c.subtotal(),2)==round(expected,2)

# Total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('item',100.0,1)
    subtotal=c.subtotal() # 100
    total=c.total(member=False,coupon='SAVE10')
    # after coupon: 90, shipping 60 -> 150
    assert round(total,2)==150.0

# Empty cart total is 0

def test_total_empty_cart():
    c=cart.Cart()
    assert c.total()==0.0
