import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------------- Tests for functions --------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -5, 105 ])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk discount percentages
@pytest.mark.parametrize(
    "quantity,expected",
    [ (9,0), (10,5), (51,10), (120,15) ]
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [ 0, -5 ])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# coupon parsing
@pytest.mark.parametrize(
    "code,expected",
    [ ("SAVE10",10), ("save1",1), ("  SaVe50  ",50) ]
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [ "BADCODE", "SA-10", "SAVE0", "SAVE51", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (0, False, 60), (999.99, False, 60), (1000, False, 0),
      (500, True, 30) ]
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    shipping_fee(-5)

# ----------------- Tests for Cart class --------------------------------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("apple", 2.0, 3)
    assert cart.items() == {"apple":3}

    # adding same item increases quantity and unit price must match
    cart.add_item("apple", 2.0, 2)
    assert cart.items()["apple"] == 5

    with pytest.raises(ValueError):
        cart.add_item("apple", 1.9, 1)  # different unit price

def test_cart_subtotal_bulk_discount():
    cart = Cart()
    cart.add_item("widget", 10.0, 10)
    assert cart.subtotal() == round(10*10 * 0.95,2)   # 5% discount

    cart.remove_item("widget", 5)
    assert cart.items()["widget"] == 5
    # No bulk discount for quantity<10
    assert cart.subtotal() == 50.0

# coupon and shipping logic according to spec (corrected behaviour)

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("banana", 20.0, 1)
    # subtotal 20, no bulk discount
    assert cart.subtotal() == 20.0

    # apply coupon 10%
    amount_after_coupon = round(20.0 * 0.9,2)  # 18.0
    shipping = shipping_fee(20.0, member=False)
    expected_total = round(amount_after_coupon + shipping,2)
    assert cart.total(coupon="SAVE10") == expected_total

# check that an empty cart returns zero cost and no shipping

def test_empty_cart_costs_zero():
    cart = Cart()
    assert cart.total() == 0

# member discounts on shipping

def test_member_shipping_discount():
    cart = Cart()
    cart.add_item("item", 100.0, 1)
    # subtotal 100 < free shipping threshold
    total_nonmember = round(100.0 + shipping_fee(100.0),2)
    assert cart.total(member=False) == total_nonmember
    total_member = round(100.0 + shipping_fee(100.0, member=True),2)
    assert cart.total(member=True) == total_member

# ensure that coupon invalid raises ValueError in total

def test_cart_total_invalid_coupon():
    cart = Cart()
    cart.add_item("gadget", 50.0,1)
    with pytest.raises(ValueError):
        cart.total(coupon="BAD")
