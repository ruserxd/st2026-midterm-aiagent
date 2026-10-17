import math
import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Helper for floating equality
EPS = 1e-9

def assert_almost_equal(a, b, *, msg=None):
    assert abs(a - b) < EPS, msg or f"{a!r} != {b!r}" 

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.456, 20, round(123.456 * 0.8, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity, expected",
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
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "10"])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE25 ", 25),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "ABCD10", "SAVEX", 123])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
# We need to know the constants used in cart module; import them
from cart import FREE_SHIPPING_THRESHOLD, SHIPPING_BASE

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, SHIPPING_BASE),
        (999.99, False, SHIPPING_BASE),
        (1000, False, 0),
        (1500, True, 0),
        (500, True, SHIPPING_BASE / 2),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_initially_empty():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0


def test_add_and_remove_items_basic():
    c = Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == round(1.0 * 3 - bulk_discount_percent(3) * 1.0 * 3 / 100, 2)

    # Adding same item increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items()["apple"] == 5

    # Removing part of quantity
    c.remove_item("apple", 3)
    assert c.items()["apple"] == 2

    # Removing more than remaining should delete item
    c.remove_item("apple", 2)
    assert "apple" not in c.items()

    with pytest.raises(KeyError):
        c.remove_item("banana")


def test_add_same_name_different_price_raises():
    c = Cart()
    c.add_item("milk", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("milk", 3.0, 1)


def test_cart_subtotal_bulk_discount_application():
    c = Cart()
    # 10 units of item A at $5 each => bulk discount 5%
    c.add_item("A", 5.0, 10)
    line_total = 5.0 * 10
    discounted = apply_discount(line_total, 5)  # 5% off
    assert math.isclose(c.subtotal(), round(discounted,2), rel_tol=1e-9)


def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("widget", 100.0, 10)  # subtotal before discount: 1000, bulk discount 5% => 950
    # Member and coupon SAVE20 => 20% off subtotal after shipping? No, shipping based on original subtotal 950 (not free)
    amount_before_coupon = c.subtotal()
    assert math.isclose(amount_before_coupon, 950.0, rel_tol=1e-9)
    discounted_amount = apply_discount(amount_before_coupon, parse_coupon("SAVE20"))
    shipping = shipping_fee(amount_before_coupon, member=True)  # subtotal <1000 => fee 30
    expected_total = round(discounted_amount + shipping,2)
    assert c.total(member=True, coupon="save20") == expected_total

# Test that total() returns 0 for empty cart (no shipping)
def test_empty_cart_no_shipping():
    c = Cart()
    # Even with a member flag or coupon, result should be 0
    assert c.total(member=True, coupon="SAVE10") == 0
