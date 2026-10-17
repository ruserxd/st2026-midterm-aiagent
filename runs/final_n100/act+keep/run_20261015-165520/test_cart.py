import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper functions ----------

def almost_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---------- Tests for apply_discount ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.99, 5, 94.99),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 101, 150],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent ----------

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (15, 5),
        (50, 10),
        (70, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_percent_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        ("   SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",  # below min
        "SAVE51",  # above max
        "DISCOUNT10",  # wrong prefix
        "SAVEXX",  # non-numeric
        "" ,  # empty
        "   ",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Tests for shipping_fee ----------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (2000, False, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("Apple", 0.5, quantity=3)
    cart.add_item("Banana", 0.2)
    assert cart.items() == [(
        "Apple",
        0.5,
        3,
    ), (
        "Banana",
        0.2,
        1,
    )]

def test_cart_remove_item():
    cart = Cart()
    cart.add_item("Orange", 0.8, quantity=4)
    cart.remove_item("Orange", quantity=2)
    assert cart.items() == [("Orange", 0.8, 2)]
    # removing more than exists removes the item entirely
    cart.remove_item("Orange", quantity=5)
    assert cart.items() == []

def test_cart_subtotal_and_total_without_discount():
    cart = Cart()
    cart.add_item("Shirt", 20, quantity=2)   # subtotal 40
    cart.add_item("Pants", 50, quantity=1)   # subtotal 90
    assert cart.subtotal() == 90
    # total without coupon or member: subtotal + shipping(60) = 150
    assert cart.total() == pytest.approx(150.0)

def test_cart_total_with_coupon_and_member():
    cart = Cart()
    cart.add_item("Shoes", 200, quantity=1)
    # subtotal 200 -> coupon SAVE10 gives 20 off => 180
    # shipping fee: subtotal after discount is 180 (<1000), member True => 30
    assert cart.total(member=True, coupon="SAVE10") == pytest.approx(210.0)

# ---------- Edge case: empty cart ----------

def test_empty_cart_total():
    cart = Cart()
    assert cart.total() == 0.0
