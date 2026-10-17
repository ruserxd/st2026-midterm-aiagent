import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- tests for helper functions -----

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (0, 10, 0.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

# boundary and error tests for apply_discount
@pytest.mark.parametrize(
    "price,percent",
    [(-10, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# error for negative or zero quantity
@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25 ", 25),
        ("  SaVe50  ", 50),
        ("sAvE1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "INVALID", "10SAVE"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal, False)

# ----- tests for Cart class -----

def create_cart_with_items():
    c = Cart()
    c.add_item("Apple", 1.0, quantity=5)   # subtotal 5
    c.add_item("Banana", 0.5, quantity=10) # subtotal 5
    return c

# Test items list reflects additions and removals

def test_cart_add_and_remove():
    cart = Cart()
    cart.add_item("Book", 12.99)
    assert len(cart.items()) == 1
    cart.remove_item("Book")
    assert cart.items() == []

# subtotal calculation

def test_subtotal():
    cart = create_cart_with_items()
    assert cart.subtotal() == pytest.approx(10.0)

# total without coupon or membership

def test_total_simple():
    cart = create_cart_with_items()
    # subtotal 10, shipping 60 (non-member), no coupon => 70
    assert cart.total(member=False) == pytest.approx(70.0)

# member reduces shipping

def test_total_member_shipping_free_above_threshold():
    cart = Cart()
    cart.add_item("Laptop", 1200)
    # subtotal 1200 >=1000 -> free shipping for both
    assert cart.total(member=True) == pytest.approx(1200.0)

# coupon reduces amount then adds shipping

def test_total_with_coupon():
    cart = Cart()
    cart.add_item("Phone", 500)
    # subtotal 500, apply SAVE10 -> 450, shipping 60 (non-member) => 510
    assert cart.total(coupon="SAVE10") == pytest.approx(510.0)

# coupon with member shipping half fee

def test_total_with_coupon_member():
    cart = Cart()
    cart.add_item("Tablet", 300)
    # subtotal 300, apply SAVE20 -> 240, shipping 30 => 270
    assert cart.total(coupon="SAVE20", member=True) == pytest.approx(270.0)

# invalid coupon raises ValueError

def test_total_invalid_coupon():
    cart = Cart()
    cart.add_item("Item", 10)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

# empty cart total is zero (no shipping)

def test_empty_cart_total_zero():
    cart = Cart()
    assert cart.total() == pytest.approx(0.0)
