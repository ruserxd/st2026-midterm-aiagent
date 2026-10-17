import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------
# apply_discount tests
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.456, 10, round(111.1104,2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

# invalid inputs
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    ["ten", None, -5, 150],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ----------
# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (30, 5),
        (50, 10),
        (75, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----------
# parse_coupon tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25 ", 25),
        ("   SaVe1  ", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "HELLO", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----------
# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----------
# Cart class tests
@pytest.fixture
def empty_cart():
    return Cart()

# adding items

def test_add_item_basic(empty_cart):
    cart = empty_cart
    cart.add_item("apple", 2.0, 3)
    assert cart.items() == {"apple": 3}
    # add more of same item with same price
    cart.add_item("apple", 2.0, 2)
    assert cart.items() == {"apple": 5}


def test_add_item_price_mismatch(empty_cart):
    cart = empty_cart
    cart.add_item("banana", 1.0)
    with pytest.raises(ValueError):
        cart.add_item("banana", 2.0)

# invalid quantity/unit price
@pytest.mark.parametrize(
    "unit_price,quantity",
    [(-1, 5), (1, -3), (1, 0), (None, 1)],
)
def test_add_item_invalid(unit_price, quantity):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("item", unit_price, quantity)

# removing items

def test_remove_item_basic(empty_cart):
    cart = empty_cart
    cart.add_item("cherry", 1.5, 4)
    cart.remove_item("cherry", 2)
    assert cart.items() == {"cherry": 2}
    # remove remaining
    cart.remove_item("cherry", 2)
    assert "cherry" not in cart.items()


def test_remove_item_not_in_cart(empty_cart):
    cart = empty_cart
    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")

# subtotal calculations

def test_subtotal_no_discount(empty_cart):
    cart = empty_cart
    cart.add_item("book", 10.0, 2)
    assert cart.subtotal() == 20.0


def test_subtotal_with_bulk_discount(empty_cart):
    cart = empty_cart
    # 12 units => 5% bulk discount per unit
    cart.add_item("pen", 3.0, 12)
    expected_before_discount = 36.0
    discounted = apply_discount(expected_before_discount, 5)  # 34.2
    assert round(cart.subtotal(), 2) == round(discounted, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping(empty_cart):
    cart = empty_cart
    cart.add_item("toy", 150.0, 1)   # subtotal 150
    # no bulk discount
    # apply coupon SAVE10 -> 10% off
    subtotal_after_coupon = apply_discount(150, 10)  # 135
    shipping = shipping_fee(subtotal_after_coupon)
    expected_total = round(subtotal_after_coupon + shipping, 2)
    assert cart.total(coupon="SAVE10") == expected_total

# member free shipping over threshold

def test_member_free_shipping(empty_cart):
    cart = empty_cart
    cart.add_item("expensive", 1200.0, 1)
    # subtotal 1200 -> free shipping
    assert cart.total(member=True) == 1200.0

# empty cart costs zero

def test_empty_cart_total(empty_cart):
    assert empty_cart.total() == 0
