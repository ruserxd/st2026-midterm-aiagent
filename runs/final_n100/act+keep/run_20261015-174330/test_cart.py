import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# ---------- Helper functions for assertions -----------

# Floating point comparison with rounding to 2 decimals
round2 = lambda x: round(x + 1e-10, 2)  # tiny epsilon to avoid issues

# ------------------ Test apply_discount -----------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 50, 25.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (10, -5), (10, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ----------------- Test bulk_discount_percent -----------

@pytest.mark.parametrize(
    "quantity,expected",
    [
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

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----------------- Test parse_coupon -------------------

valid_codes = ["SAVE10", "save10", " SAVE10 ", "Save5"]
for code in valid_codes:
    # dynamic generation using parametrize? use separate tests.
    pass

@pytest.mark.parametrize(
    "code,expected",
    [("SAVE10", 10), ("save5", 5), (" SAVE15 ", 15)],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE10", "SAVE0", "SAVE51", "ABC123", "save-5", "SAVExx", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ------------------ Test Cart class ---------------------

@pytest.fixture
def empty_cart():
    return Cart()

def test_add_item_valid(empty_cart):
    cart = empty_cart
    cart.add_item("apple", 1.0, 3)
    assert cart.items() == {"apple": 3}
    # adding same item increases quantity
    cart.add_item("apple", 1.0, 2)
    assert cart.items() == {"apple": 5}


def test_add_item_invalid_price(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", -1.0, 1)


def test_add_item_invalid_quantity(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 1.0, 0)


def test_add_item_price_mismatch(empty_cart):
    cart = empty_cart
    cart.add_item("orange", 2.0, 1)
    with pytest.raises(ValueError):
        cart.add_item("orange", 3.0, 1)


def test_remove_item_valid(empty_cart):
    cart = empty_cart
    cart.add_item("pear", 1.5, 4)
    cart.remove_item("pear", 2)
    assert cart.items() == {"pear": 2}
    cart.remove_item("pear", 2)
    assert cart.items() == {}


def test_remove_item_not_in_cart(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent", 1)

# ----------------- Subtotal calculation -----------------

@pytest.mark.parametrize(
    "items,expected",
    [
        ({"item": (10.0, 5)}, 50.0),  # no discount
        ({"item": (10.0, 10)}, 95.0),  # 5% bulk on 10 units: 10*10=100 -> 5% off => 95
        ({"item1": (20.0, 50), "item2": (5.0, 3)}, 1075.0),
    ],
)
def test_subtotal(items, expected):
    cart = Cart()
    for name, (price, qty) in items.items():
        cart.add_item(name, price, qty)
    assert round2(cart.subtotal()) == round2(expected)

# ----------------- Total calculation ---------------------

@pytest.mark.parametrize(
    "cart_setup,member,coupon,total",
    [
        (lambda: Cart(), False, None, 0.0),  # empty cart
        (
            lambda: (c := Cart()).add_item("x", 20.0, 2) or c,
            False,
            None,
            40.0 + shipping_fee(40.0),
        ),
        (
            lambda: (c := Cart()).add_item("y", 100.0, 10) or c,
            True,
            "SAVE5",
            # subtotal 950 -> coupon 5% => 902.5 -> shipping on 902.5
            round2(902.5 + shipping_fee(902.5)),
        ),
    ],
)
def test_total(cart_setup, member, coupon, total):
    cart = cart_setup()
    result = cart.total(member=member, coupon=coupon)
    assert round2(result) == round2(total)

# ----------------- Shipping fee tests -------------------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0.0, False, 0.0),
        (49.99, False, 5.0),
        (50.00, False, 0.0),
        (75.00, True, 0.0),
        (120.00, True, 0.0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member=member) == expected

# ----------------- Edge cases for total with coupon ----

def test_total_coupon_invalid(empty_cart):
    cart = empty_cart
    cart.add_item("a", 10.0, 1)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ----------------- Rounding behavior ---------------------------------

def test_rounding_behavior(empty_cart):
    cart = empty_cart
    # add item leading to subtotal requiring rounding
    cart.add_item("item", 0.3333, 3)  # 0.9999 -> round to 1.00 after discount? no bulk discount
    assert round2(cart.subtotal()) == 1.0
    total = cart.total()
    assert round2(total) == 1.0 + shipping_fee(1.0)
