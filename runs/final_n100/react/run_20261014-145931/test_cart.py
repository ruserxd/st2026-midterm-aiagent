import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---- apply_discount tests ----
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),            # example
        (100, 0, 100.0),              # no discount
        (50, 100, 0.0),               # full price off
        (123.45, 25, round(123.45 * 0.75, 2)),
    ],
)
def test_apply_discount_success(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (50, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---- bulk_discount_percent tests ----
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -3],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---- parse_coupon tests ----
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30  ", 30),
    ],
)
def test_parse_coupon_success(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "SAVEXX", "20SAVE", ""],
)
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---- shipping_fee tests ----
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200, False, 0),
        (1000, True, 0),
        (999.99, False, 60),
        (200, True, 30),
        (500, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal, False)

# ---- Cart tests ----
@pytest.fixture
def cart():
    return Cart()

def test_cart_initial_empty(cart):
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 60  # shipping for empty cart is 60 for non-member

def test_cart_add_and_remove(cart):
    cart.add_item("Apple", 100, 2)
    cart.add_item("Banana", 50, 3)
    assert cart.items()["Apple"] == (100, 2)
    assert cart.items()["Banana"] == (50, 3)

    # subtotal should be 100*2 + 50*3 = 300 + 150 = 450
    assert cart.subtotal() == 450

    # total without member or coupon: 450 + shipping(60) = 510
    assert cart.total() == 510

    # remove some quantity
    cart.remove_item("Apple", 1)
    assert cart.items()["Apple"] == (100, 1)
    assert cart.subtotal() == 350

    # remove all of an item
    cart.remove_item("Banana", 3)
    assert "Banana" not in cart.items()
    assert cart.subtotal() == 100

    # apply member discount: subtotal 100 < 1000, shipping 30 => 130 total
    assert cart.total(member=True) == 130

    # coupon test: SAVE10 should give 10% off the subtotal before shipping
    # subtotal is 100, after 10% -> 90, shipping 60 => 150
    assert cart.total(coupon="SAVE10") == 150

    # combined member + coupon
    assert cart.total(member=True, coupon="SAVE10") == 120

# Edge case: adding same item multiple times updates quantity
def test_cart_add_same_item(cart):
    cart.add_item("Milk", 200)
    cart.add_item("Milk", 200, 2)  # should increase to qty=3
    assert cart.items()["Milk"] == (200, 3)
    assert cart.subtotal() == 600

# Removing more than existing quantity removes item entirely
def test_cart_remove_more_than_existing(cart):
    cart.add_item("Bread", 150, 2)
    cart.remove_item("Bread", 5)  # remove all
    assert "Bread" not in cart.items()
    assert cart.subtotal() == 0

# Removing non-existent item should raise KeyError (implementation dependent)
def test_cart_remove_nonexistent(cart):
    with pytest.raises(KeyError):
        cart.remove_item("NonExistent", 1)
