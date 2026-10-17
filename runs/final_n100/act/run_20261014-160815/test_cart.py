import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- apply_discount -----
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

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-0.1, 100.1, 200])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (20, 10),
        (50, 10),
        (60, 15),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----- parse_coupon -----
valid_codes = {
    "SAVE10": 10,
    "save25": 25,
    "   SaVe5  ": 5,
}

@pytest.mark.parametrize("code,expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = ["SAVEXX", "SAVE0", "SAVE51", "", "10SAVE", 123]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Cart class -----

@pytest.fixture
def cart():
    return Cart()

def test_cart_initially_empty(cart):
    assert cart.items() == {}
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0

# adding items

def test_add_item_new(cart):
    cart.add_item("apple", 1.5, 2)
    assert cart.items() == {"apple": 2}
    expected = 1.5 * 2
    assert cart.subtotal() == round(expected, 2)

def test_add_item_existing_same_price(cart):
    cart.add_item("banana", 0.8, 3)
    cart.add_item("banana", 0.8, 2)
    assert cart.items()["banana"] == 5
    expected = 0.8 * 5
    assert cart.subtotal() == round(expected, 2)

def test_add_item_existing_different_price(cart):
    cart.add_item("cherry", 2.0)
    with pytest.raises(ValueError):
        cart.add_item("cherry", 3.0)

# invalid add params
@pytest.mark.parametrize(
    "unit_price,quantity",
    [(-1, 1), (5, -1), (5, 0), (5, 2.5)],
)
def test_add_item_invalid_params(cart, unit_price, quantity):
    with pytest.raises(ValueError):
        cart.add_item("mango", unit_price, quantity)

# removing items

def test_remove_item_partial(cart):
    cart.add_item("peach", 2.0, 4)
    cart.remove_item("peach", 2)
    assert cart.items()["peach"] == 2
    expected = 2.0 * 2
    assert cart.subtotal() == round(expected, 2)

def test_remove_item_all(cart):
    cart.add_item("plum", 3.0, 1)
    cart.remove_item("plum")
    assert "plum" not in cart.items()

def test_remove_nonexistent(cart):
    with pytest.raises(KeyError):
        cart.remove_item("orange")

# subtotal with bulk discount

def test_subtotal_bulk_discount(cart):
    cart.add_item("kiwi", 1.0, 12)
    expected = 1.0 * 12 * (1 - 0.05)
    assert cart.subtotal() == round(expected, 2)

# total calculation with coupon and shipping

def test_total_with_coupon_and_shipping(cart):
    cart.add_item("bread", 20.0, 3)
    total_without_coupon = 60 + shipping_fee(60)
    assert cart.total() == round(total_without_coupon, 2)

    total_with_coupon = (60 * 0.9) + shipping_fee(60 * 0.9)
    assert cart.total(coupon="SAVE10") == round(total_with_coupon, 2)

# total on empty cart

def test_total_empty_cart(cart):
    assert cart.total() == 0.0

# invalid coupon

def test_total_invalid_coupon(cart):
    cart.add_item("milk", 5.0)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")
