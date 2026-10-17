import pytest
import cart

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -1, 200])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-1,1.5,"a"])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon
valid_coupons = {
    "SAVE10":10,
    "save20 ":20,
    "  SaVe50":50,
}
@pytest.mark.parametrize("code,exp", valid_coupons.items())
def test_parse_coupon_valid(code, exp):
    assert cart.parse_coupon(code) == exp

invalid_coupons = ["SAV10","SAVE0","SAVE51","ABCD10", "SAVE-5", "  "]
@pytest.mark.parametrize("code", invalid_coupons)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0,False,60),
    (999.99,False,60),
    (1000,False,0),
    (1500,True,30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart operations
def test_cart_basic_operations():
    c = cart.Cart()
    assert c.items() == {}
    # add item
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple":3}
    # adding same item with same price increases quantity
    c.add_item("apple", 2.0, 2)
    assert c.items()["apple"] == 5
    # add different item
    c.add_item("banana",1.5,4)
    assert c.items() == {"apple":5,"banana":4}
    # subtotal with no discount for apple (qty<10), banana qty>=4 => no bulk
    assert c.subtotal() == round(2.0*5 + 1.5*4,2)
    # remove item partially
    c.remove_item("apple",2)
    assert c.items()["apple"] ==3
    # remove all quantity to zero
    c.remove_item("banana",4)
    assert "banana" not in c.items()
    # removing non-existent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("pear",1)

# test bulk discount effect on subtotal
def test_cart_bulk_discount():
    c = cart.Cart()
    c.add_item("widget",10.0,10)  # qty=10 =>5% discount
    assert c.subtotal() == round(10.0*10*(1-0.05),2)
    c.add_item("gadget",20.0,50)  # qty=50 =>10%
    expected = round(10.0*10*(1-0.05)+20.0*50*(1-0.10),2)
    assert c.subtotal() == expected

# test total with coupon and shipping
def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item",100.0,1)
    # subtotal 100 -> no bulk discount
    subtotal=100.0
    # apply coupon SAVE10 => 90
    total_before_ship=90.0
    # shipping fee for non-member: 60 => total 150
    assert c.total(coupon="SAVE10") == round(total_before_ship+cart.shipping_fee(subtotal),2)

# test empty cart total
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
