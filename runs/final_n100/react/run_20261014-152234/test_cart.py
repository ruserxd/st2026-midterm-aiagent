import pytest
from cart import Cart, parse_coupon, shipping_fee

def create_cart(items):
    c = Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# parse_coupon tests – only uppercase valid

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" SAVE20 ") == 20
    assert parse_coupon("SAVE30") == 30
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError): parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError): parse_coupon("SAVE0")
    with pytest.raises(ValueError): parse_coupon("SAVE51")
    with pytest.raises(ValueError): parse_coupon("SAVE-5")
    with pytest.raises(ValueError): parse_coupon("SAVEXX")

# shipping_fee tests unchanged

def test_shipping_fee_regular():
    assert shipping_fee(999) == 60
    assert shipping_fee(0) == 60
    assert shipping_fee(500, member=True) == 30

def test_shipping_fee_free():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500, member=True) == 0

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError): shipping_fee(-1)

# Cart subtotal & items

def test_cart_subtotal_and_items():
    cart = create_cart([("apple",100,3),("banana",50,4)])
    assert cart.subtotal() == 500
    assert cart.items() == {"apple":3,"banana":4}

# Cart.total tests according to spec

def test_cart_total_no_coupon():
    cart = create_cart([("widget",200,1)])
    assert cart.total() == 260.00
    assert cart.total(member=True) == 230.00

def test_cart_total_with_valid_coupon():
    cart = create_cart([("gadget",500,2)])
    assert cart.total(coupon="SAVE10") == 900.00
    cart = create_cart([("small_item",400,3)])
    assert cart.total(coupon="SAVE10") == 1080.00
    cart = create_cart([("odd",333.33,1)])
    assert cart.total(coupon="SAVE10") == 360.00

def test_cart_total_invalid_coupon():
    cart = create_cart([("test",100,1)])
    with pytest.raises(ValueError): cart.total(coupon="BADCODE")

def test_empty_cart_total():
    cart = Cart()
    assert cart.subtotal() == 0
    assert cart.total() == 0.00
