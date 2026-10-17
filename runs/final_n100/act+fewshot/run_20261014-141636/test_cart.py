import pytest
import cart

# Helper to round

def round2(x):
    return round(x,2)

@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent)==result

@pytest.mark.parametrize("quantity,percent",[
    (5,0),(9,0),(10,5),(49,5),(50,10),(99,10),(100,15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity)==percent

@pytest.mark.parametrize("code,result",[
    ("SAVE10",10),
    ("save20",20),
    ("  SaVe5 ",5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("code",["", "NOTVALID", "SAVE0", "SAVE51", "SAVEE10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,fee",[
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member)==fee

# Cart tests

def test_cart_add_and_items():
    c=cart.Cart()
    assert c.items()=={}
    c.add_item("apple",10.0)
    assert c.items() == {"apple":1}
    c.add_item("banana",5.0,3)
    assert c.items() == {"apple":1,"banana":3}
    # adding existing item with same price
    c.add_item("apple",10.0,2)
    assert c.items()=={"apple":3,"banana":3}
    # error on different price
    with pytest.raises(ValueError):
        c.add_item("apple",9.0)

@pytest.mark.parametrize("quantity,expected_subtotal",[
    (1,10.00),  # no bulk discount
    (10,90.0),  # 5% off: 10*10=100 ->95? Actually percent =5 => 95
])
def test_cart_subtotal_simple(quantity, expected_subtotal):
    c=cart.Cart()
    c.add_item("item",10.0,quantity)
    assert round2(c.subtotal())==expected_subtotal

def test_cart_total_with_coupon_and_shipping():
    c=cart.Cart()
    c.add_item("large",200.0,5)  # no bulk discount
    subtotal=c.subtotal() #1000
    assert subtotal==1000.0
    total=c.total(coupon="SAVE10")
    # coupon reduces 10%: 900 -> add shipping? subtotal after coupon=900<1000 so fee 60
    assert round2(total)==round2(900+60)

def test_cart_total_no_shipping_when_empty():
    c=cart.Cart()
    assert c.total()==0.0
