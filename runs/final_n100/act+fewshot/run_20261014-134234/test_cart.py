import pytest
import cart

# Tests for apply_discount
def test_apply_discount():
    assert cart.apply_discount(200,15)==170.0
    assert cart.apply_discount(100,0)==100.0
    assert cart.apply_discount(50,100)==0.0

@pytest.mark.parametrize("price,percent", [(-1,10),(100,-5),(100,105)])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# Tests for bulk_discount_percent
def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9)==0
    assert cart.bulk_discount_percent(10)==5
    assert cart.bulk_discount_percent(49)==5
    assert cart.bulk_discount_percent(50)==10
    assert cart.bulk_discount_percent(99)==10
    assert cart.bulk_discount_percent(100)==15

@pytest.mark.parametrize("qty", [0,-5,"a"])   # non‑positive or not int
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Tests for parse_coupon
def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10")==10
    assert cart.parse_coupon("save20")==20
    assert cart.parse_coupon(" SAVE30 ")==30

@pytest.mark.parametrize("code", ["SAVEXX","SAVE0","SAVE51","NOTA10","  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
def test_shipping_fee():
    assert cart.shipping_fee(1000,False)==0.0
    assert cart.shipping_fee(999.99,False)==60.0
    assert cart.shipping_fee(200,True)==30.0

@pytest.mark.parametrize("subtotal", [-10,-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
def test_cart_initially_empty():
    c=cart.Cart()
    assert c.items()=={}
    assert c.subtotal()==0.0
    assert c.total()==0.0

def test_add_and_remove_items():
    c=cart.Cart()
    c.add_item("apple",1.5,quantity=3)
    c.add_item("banana",2.0)
    assert c.items()["apple"]==(1.5,3)
    assert c.items()["banana"]==(2.0,1)
    assert c.subtotal()==1.5*3+2.0
    c.remove_item("apple",quantity=2)
    assert c.items()["apple"]==(1.5,1)
    c.remove_item("apple")
    assert "apple" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("orange")

# Total calculation with member and coupon
def test_total_simple():
    c=cart.Cart()
    c.add_item("item",10.0,quantity=5)
    total=c.total(member=False,coupon=None)
    assert total==110.0

# test with member discount and bulk discount
def test_total_with_bulk_and_coupon():
    c=cart.Cart()
    c.add_item("widget",20.0,quantity=120)
    total=c.total(member=True,coupon="SAVE10")
    expected=2400*0.85*0.90
    assert round(total,2)==round(expected,2)
