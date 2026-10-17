import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper Assertions ----------

def assert_round(val, expected):
    """Helper to compare rounded values."""
    assert round(val, 2) == expected

# ===================== TESTS ======================

# apply_discount tests
@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 10, 111.11),  # 123.45 * 0.9 = 111.105 rounded to 2 decimals
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

# invalid inputs for apply_discount
@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk_discount_percent tests
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
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# invalid inputs for bulk_discount_percent
@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon tests (case-insensitive and whitespace tolerant)
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SaVe5 ", 5),
        ("SAVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# invalid coupon codes
@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "NOPE10", "save-5", "1234", "SAVEX"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# invalid subtotal for shipping_fee
@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart class tests

def test_cart_initial_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# adding items and subtotal calculations with bulk discount
def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", unit_price=1.00, quantity=9)
    # no bulk discount
    assert c.subtotal() == 9.00
    c.add_item("apple", unit_price=1.00, quantity=2)  # total 11 => 5% discount
    expected = round(1.00 * 11 * 0.95, 2)
    assert c.subtotal() == expected
    # add another item with higher bulk discount
    c.add_item("banana", unit_price=2.00, quantity=50)  # 10% bulk discount
    banana_total = round(2.00 * 50 * 0.90, 2)
    assert c.subtotal() == round(expected + banana_total, 2)

# item removal and negative quantity handling
def test_cart_remove_items():
    c = Cart()
    c.add_item("orange", unit_price=3.00, quantity=5)
    c.remove_item("orange", quantity=2)
    assert c.items()["orange"] == 3
    # remove more than existing -> item removed
    c.remove_item("orange", quantity=4)
    assert "orange" not in c.items()
    # removing non-existent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("pear")

# cart total with coupon and member shipping
def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("widget", unit_price=200, quantity=5)  # no bulk discount
    subtotal = 200 * 5
    # apply 10% coupon => 180
    amount_after_coupon = round(subtotal * 0.90, 2)
    shipping = shipping_fee(amount_after_coupon, member=True)  # half of 60
    total_expected = round(amount_after_coupon + shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == total_expected

# cart total for empty cart (no shipping)
def test_cart_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0

# Test that add_item validates unit price and quantity types
@pytest.mark.parametrize(
    "unit_price, quantity",
    [(-1, 5), (10, -3), (10.5, 2)],
)
def test_add_item_invalid(unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("gadget", unit_price=unit_price, quantity=quantity)

# Test that adding item with mismatched price raises ValueError
def test_add_item_mismatched_price():
    c = Cart()
    c.add_item("thing", 5.00, 2)
    with pytest.raises(ValueError):
        c.add_item("thing", 6.00, 1)

# Test remove_item reduces quantity properly and doesn't raise for zero remaining
def test_remove_exact_quantity():
    c = Cart()
    c.add_item("test", 10.0, 3)
    c.remove_item("test", 3)  # should leave cart empty without error
    assert "test" not in c.items()

# Test subtotal rounding behavior with bulk discount that yields fraction
def test_subtotal_rounding():
    c = Cart()
    c.add_item("special", unit_price=99.99, quantity=10)  # 5% discount
    raw = 99.99 * 10 * 0.95
    assert c.subtotal() == round(raw, 2)
