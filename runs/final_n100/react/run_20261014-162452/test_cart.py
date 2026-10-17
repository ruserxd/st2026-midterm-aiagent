import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Helper function for approximate equality

def approx_equal(a, b, eps=1e-6):
    return abs(a - b) < eps

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (123.456, 10, round(123.456 * 0.9, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize(
    "price, percent",
    [(-10.0, 10), (50.0, -5), (50.0, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("   SaVe20  ", 20),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "",
        "SAVE0",
        "SAVE51",
        "DISCOUNT10",
        "save-5",
        "  SAVE10X  ",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (500.0, False, 60),
        (500.0, True, 30),
        (1000.0, False, 0),
        (1200.0, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10.0],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------
def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == []
    assert cart.subtotal() == 0.0

    cart.add_item("apple", 100, quantity=3)
    cart.add_item("banana", 200)
    assert len(cart.items()) == 2
    assert cart.subtotal() == 500.0

    cart.remove_item("apple", quantity=2)
    items = {name: (price, qty) for name, price, qty in cart.items()}
    assert items["apple"] == (100, 1)
    assert cart.subtotal() == 300.0

    cart.remove_item("banana", quantity=5)
    names = [name for name, _, _ in cart.items()]
    assert "banana" not in names
    assert cart.subtotal() == 100.0


def test_cart_total_no_discount_and_shipping():
    cart = Cart()
    cart.add_item("item", 200, quantity=4)  # subtotal 800
    total_without_member = cart.total(member=False)
    assert approx_equal(total_without_member, 860.0)

    total_with_member = cart.total(member=True)
    assert approx_equal(total_with_member, 830.0)


def test_cart_total_with_coupon_and_bulk_discount():
    cart = Cart()
    cart.add_item("widget", 50, quantity=120)  # subtotal before discount 6000
    bulk_percent = bulk_discount_percent(120)
    assert bulk_percent == 15
    discounted_unit = apply_discount(50, bulk_percent)
    expected_subtotal = round(discounted_unit * 120, 2)
    coupon_percent = parse_coupon("SAVE20")
    final_unit = apply_discount(discounted_unit, coupon_percent)
    expected_total = round(final_unit * 120, 2) + shipping_fee(expected_subtotal)
    total = cart.total(coupon="SAVE20")
    assert approx_equal(total, expected_total)


def test_cart_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("item", 100)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")
