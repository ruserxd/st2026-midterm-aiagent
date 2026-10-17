import re
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
        (123.456, 10, round(123.456 * 0.9, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

# Boundary / error cases
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    ["abc", -5, 105],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

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

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# invalid codes
@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "DISCOUNT10", "SAVEBAR"])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (50, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

@pytest.fixture
def cart():
    return Cart()


def test_cart_initially_empty(cart):
    assert cart.items() == {}
    assert cart.subtotal() == 0.0
    assert cart.total() == pytest.approx(60)  # shipping fee for empty subtotal


def test_add_and_remove_items(cart):
    cart.add_item("apple", unit_price=100, quantity=2)
    assert cart.items()["apple"] == (100, 2)
    assert cart.subtotal() == 200.0
    # add more of same item
    cart.add_item("apple", unit_price=100, quantity=3)
    assert cart.items()["apple"] == (100, 5)
    # remove part
    cart.remove_item("apple", quantity=2)
    assert cart.items()["apple"] == (100, 3)
    # remove all
    cart.remove_item("apple")
    assert "apple" not in cart.items()


def test_cart_total_with_member_and_coupon(cart):
    cart.add_item("widget", unit_price=200, quantity=5)  # subtotal = 1000
    # member gets free shipping
    assert cart.total(member=True) == pytest.approx(1000)
    # non-member shipping fee 60 + subtotal
    assert cart.total() == pytest.approx(1060)
    # apply coupon discount of 10%
    assert cart.total(coupon="SAVE10") == pytest.approx((1000 - 100.0) + 60)


def test_cart_total_bulk_discount(cart):
    cart.add_item("pen", unit_price=5, quantity=120)  # subtotal 600
    # bulk discount percent should be 15 for quantity >= 100
    # total = (600 * 0.85) + shipping(60) = 510 + 60 = 570
    assert cart.total() == pytest.approx(570)

# Test that Cart.total uses apply_discount and bulk_discount_percent appropriately

def test_cart_total_uses_bulks_and_shipping(cart):
    # add item with quantity 10 -> 5% discount
    cart.add_item("note", unit_price=20, quantity=10)  # subtotal 200
    expected = round(200 * 0.95 + 60, 2)
    assert cart.total() == pytest.approx(expected)

# Ensure coupon parsing is case-insensitive and whitespace handled

def test_cart_coupon_whitespace_and_case(cart):
    cart.add_item("test", unit_price=100, quantity=1)
    assert cart.total(coupon=" save20 ") == pytest.approx((100 - 20.0) + 60)
    assert cart.total(coupon="SAVE5") == pytest.approx((100 - 5.0) + 60)

# Ensure ValueError for invalid coupon in total

def test_cart_total_invalid_coupon(cart):
    cart.add_item("test", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        cart.total(coupon="badcode")

# Test that subtotal rounds to two decimals

def test_subtotal_rounding(cart):
    cart.add_item("item", unit_price=33.3333, quantity=3)  # 99.9999 -> 100.0 after rounding
    assert cart.subtotal() == pytest.approx(100.0)

# Test that remove_item raises ValueError when removing more than existing

def test_remove_more_than_exists(cart):
    cart.add_item("extra", unit_price=10, quantity=2)
    with pytest.raises(ValueError):
        cart.remove_item("extra", quantity=5)

# Ensure remove_item for non-existent item raises ValueError

def test_remove_nonexistent_item(cart):
    with pytest.raises(ValueError):
        cart.remove_item("ghost")
