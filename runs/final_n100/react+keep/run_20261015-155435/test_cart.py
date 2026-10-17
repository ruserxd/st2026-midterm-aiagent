import cart
import pytest

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent",[( -1,10),(100,-5),(100,105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount tests

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5   # spec says 5 for 10-49
    assert cart.bulk_discount_percent(49) == 10
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.3)

# coupon tests

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25   # whitespace ignored per spec
    assert cart.parse_coupon("SaVe1") == 1

@ pytest.mark.parametrize("code",["NOPE","SAVE0","SAVE51","SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping tests

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0

@ pytest.mark.parametrize("subtotal",[-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_add_and_remove():
    c=cart.Cart()
    c.add_item('apple', 100, 2)
    assert c.items() == {'apple':2}
    c.remove_item('apple',1)
    assert c.items()=={'apple':1}
    c.remove_item('apple',1)
    assert c.items()=={}

@ pytest.mark.parametrize("name,price,quantity",[("pear",-10,1),("banana",5,0)])
def test_cart_add_invalid(name,price,quantity):
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, quantity)

# subtotal calculation with bulk discount

def test_subtotal_bulk():
    c=cart.Cart()
    # 10 apples at $1 each -\u003e total $10, bulk discount percent =5 =\u003e discounted to $9.5
    c.add_item('apple',1,10)
    assert c.subtotal() == 9.5

# total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item('widget',200,2) # subtotal $400, no bulk discount
    # apply coupon SAVE10 -\u003e amount $360
    amount = cart.apply_discount(400,10)
    shipping = cart.shipping_fee(amount, member=False)
    total_expected = round(amount + shipping,2)
    assert c.total(member=False,coupon='SAVE10') == total_expected

# test that removing item with quantity equal to current deletes the entry (bug detection)
def test_remove_item_equal_quantity_bug():
    c=cart.Cart()
    c.add_item('gadget',50,1)
    # remove 1 should delete entry
    c.remove_item('gadget',1)
    assert 'gadget' not in c.items()

# test total bug: shipping computed on subtotal before coupon

def test_total_shipping_bug():
    c=cart.Cart()
    c.add_item('expensive',1200,1)  # subtotal $1200
    # apply 50% discount => amount $600 which is <1000 so should incur shipping fee of 60 for non-member
    total_expected = round(cart.apply_discount(1200,50)+60,2)
    assert c.total(member=False,coupon='SAVE50') == total_expected
