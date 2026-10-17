import pytest
import cart

# ---------- apply_discount -------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding
    assert cart.apply_discount(100, 33) == 67.0   # 100*0.67 = 67

@ pytest.mark.parametrize("price,percent", [(-1,10),(50,-5),(50,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -------------------------------------

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0,-5,2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" SAVE5 ") == 5

@ pytest.mark.parametrize("code", ["SAVEX", "50", "SAVE0", "SAVE51", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(2000, member=False) == 0

@ pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

@ pytest.mark.parametrize("name,price,qty", [(
    "apple",1.00,3),("banana",2.50,1)])
def test_cart_add_item(name, price, qty):
    c = cart.Cart()
    c.add_item(name, price, qty)
    assert c.items() == {name:qty}
    # adding same item increases quantity
    c.add_item(name, price, 2)
    assert c.items()[name] == qty+2

@ pytest.mark.parametrize("name,price,qty", [(
    "apple",1.00,-1),("banana",-0.5,1)])
def test_cart_add_invalid(name, price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, qty)

@ pytest.mark.parametrize("name,price,qty,existing_qty", [(
    "apple",1.00,3,5),("banana",2.50,1,0)])
def test_cart_add_existing_price_mismatch(name, price, qty, existing_qty):
    c = cart.Cart()
    # set up existing
    if existing_qty>0:
        c.add_item(name, 1.00, existing_qty)  # different price
    with pytest.raises(ValueError):
        c.add_item(name, price, qty)

# remove item tests

def test_cart_remove():
    c = cart.Cart()
    c.add_item("apple",1.0,5)
    c.remove_item("apple",2)
    assert c.items()["apple"] == 3
    # removing more than exists removes item
    c.remove_item("apple",4)
    assert "apple" not in c.items()

@ pytest.mark.parametrize("name,qty", [("pear",1)])
def test_cart_remove_nonexistent(name, qty):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, qty)

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk():
    c = cart.Cart()
    # 10 apples at $1 each -> 5% discount => 9.5
    c.add_item("apple",1.0,10)
    # 50 bananas at $2 each -> 10% discount => 90
    c.add_item("banana",2.0,50)
    assert c.subtotal() == pytest.approx(99.5, rel=1e-9)

# total with coupon and shipping

def test_total_full_flow():
    c = cart.Cart()
    c.add_item("item",100.0,10)  # subtotal 95 (5% discount)
    total = c.total(member=True, coupon="SAVE10")
    # apply coupon: 95*0.9=85.5; shipping fee: member half of 60 =>30
    assert total == pytest.approx(115.5, rel=1e-9)

# empty cart total should be 0 no shipping

def test_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
