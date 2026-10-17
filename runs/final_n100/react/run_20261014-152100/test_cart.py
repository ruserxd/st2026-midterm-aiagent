import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------------- helper asserts -----------------

def assert_equal(a, b):
    assert a == b

# 1. apply_discount tests

def test_apply_discount_valid():
    # basic example from spec
    assert_equal(apply_discount(200, 15), 170.0)
    # zero percent
    assert_equal(apply_discount(500, 0), 500.0)
    # full discount
    assert_equal(apply_discount(400, 100), 0.0)

@ pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# 2. bulk_discount_percent tests

def test_bulk_discount_percent_values():
    assert_equal(bulk_discount_percent(9), 0)
    assert_equal(bulk_discount_percent(10), 5)
    assert_equal(bulk_discount_percent(49), 5)
    assert_equal(bulk_discount_percent(50), 10)
    assert_equal(bulk_discount_percent(99), 10)
    assert_equal(bulk_discount_percent(100), 15)

@ pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_negative_qty_raises(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# 3. parse_coupon tests

def test_parse_coupon_valid():
    assert_equal(parse_coupon("SAVE10"), 10)
    assert_equal(parse_coupon("save25"), 25)
    assert_equal(parse_coupon("   SaVe5   "), 5)

@ pytest.mark.parametrize("code", ["SAVEBAD", "12345", "save0", "save51", "", "SAVE-10"]) 
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# 4. shipping_fee tests

def test_shipping_fee_values():
    assert_equal(shipping_fee(0), 60)
    assert_equal(shipping_fee(999), 60)
    assert_equal(shipping_fee(1000), 0)
    # member half fee
    assert_equal(shipping_fee(500, member=True), 30)

@ pytest.mark.parametrize("sub", [-1, -50])
def test_shipping_fee_negative_sub_raises(sub):
    with pytest.raises(ValueError):
        shipping_fee(sub)

# 5. Cart class tests

def test_cart_initially_empty():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 60  # no items, non-member => shipping 60

def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 100, 3)
    c.add_item("banana", 200)   # default quantity=1
    assert c.items() == {"apple": (100, 3), "banana": (200, 1)}
    # subtotal: 3*100 + 1*200 = 500
    assert c.subtotal() == 500
    # total without discounts or coupon
    assert c.total(member=False) == 560  # subtotal 500 + shipping 60

    # remove some quantity
    c.remove_item("apple", 2)
    assert c.items()["apple"] == (100, 1)
    # remove more than existing -> should error? assume ValueError
    with pytest.raises(ValueError):
        c.remove_item("banana", 2)

    # test bulk discount applied via total: quantity 50+ => 10% off for that item
    c = Cart()
    c.add_item("widget", 200, 50)  # 50 items -> bulk discount 10%
    expected_sub = 200 * 50 * 0.9  # 10% off on unit price? Actually apply_discount will be used in total logic
    assert c.subtotal() == 200 * 50
    # compute expected total with shipping: subtotal after bulk discount + shipping
    # Let's just check that total is less than subtotal+shipping, indicating discount applied
    t = c.total()
    assert t < c.subtotal() + 60

def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("item", 300, 2)   # no bulk discount
    # subtotal 600
    total1 = c.total(member=True)  # shipping half: 30 -> 630
    assert total1 == 630

    # apply coupon 10% off
    total2 = c.total(member=True, coupon="SAVE10")
    # subtotal after coupon: 600*0.9=540; plus shipping 30 => 570
    assert total2 == 570

# Ensure that Cart.total raises ValueError if invalid coupon passed
@ pytest.mark.parametrize("coupon", ["INVALID", "SAVE60"]) 
def test_cart_total_invalid_coupon_raises(coupon):
    c = Cart()
    c.add_item("item", 100)
    with pytest.raises(ValueError):
        c.total(coupon=coupon)

# Edge case: adding an item that already exists should increase quantity
def test_cart_add_existing_increases_quantity():
    c = Cart()
    c.add_item("x", 50, 2)
    c.add_item("x", 50, 3)
    assert c.items()["x"] == (50, 5)
