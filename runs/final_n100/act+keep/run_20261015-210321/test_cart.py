import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

def round_two(value):
    return round(float(value), 2)

# Tests for individual functions
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SAVE30  ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [""] ,
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1500.5, True, 0),
        (999.99, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee_valid(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal,member",
    [(-10, False), (-1.5, True)],
)
def test_shipping_fee_invalid(subtotal, member):
    with pytest.raises(ValueError):
        shipping_fee(subtotal, member)

# Cart tests

def test_cart_empty_totals():
    cart = Cart()
    assert cart.items() == []
    assert cart.subtotal() == 0
    assert cart.total() == 0

def test_cart_add_and_subtotal_with_bulk_discount():
    cart = Cart()
    cart.add_item("A", 10, quantity=12)
    assert cart.items() == [("A", 10, 12)]
    expected_subtotal = round_two(10 * 12 * (1 - 0.05))
    assert cart.subtotal() == expected_subtotal

def test_cart_remove_item():
    cart = Cart()
    cart.add_item("B", 20, quantity=5)
    cart.remove_item("B", quantity=2)
    assert cart.items() == [("B", 20, 3)]
    expected_subtotal = round_two(20 * 3)
    assert cart.subtotal() == expected_subtotal

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("C", 200, quantity=5)
    subtotal = 200 * 5
    after_coupon = round_two(subtotal * (1 - 0.10))
    shipping = shipping_fee(after_coupon)
    expected_total = round_two(after_coupon + shipping)
    assert cart.total(coupon="SAVE10") == expected_total

def test_cart_total_invalid_coupon():
    cart = Cart()
    cart.add_item("D", 50, quantity=2)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# Membership handling tests

def test_cart_member_shipping_and_discount():
    cart = Cart()
    cart.add_item("E", 100, quantity=5)
    subtotal = 100 * 5
    after_coupon = subtotal
    shipping = shipping_fee(after_coupon, member=True)
    expected_total = round_two(subtotal + shipping)
    assert cart.total(member=True) == expected_total
