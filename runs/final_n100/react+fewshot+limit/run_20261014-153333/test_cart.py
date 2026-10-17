import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert apply_discount(price, percent) == expected

# Boundary and error cases for apply_discount
@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --- bulk_discount_percent ----------------------------------------------
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

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SaVe30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAV10", "SAVE0", "SAVE51", "abc", "SAVE-5", " "]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
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

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart class ---------------------------------------------------------
@pytest.fixture
def empty_cart():
    return Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.5, 3)
    assert empty_cart.items() == {"apple": 3}

def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana", 0.8, 2)
    empty_cart.add_item("banana", 0.8, 1)
    assert empty_cart.items() == {"banana": 3}

def test_add_item_same_name_different_price_raises(empty_cart):
    empty_cart.add_item("pear", 1.0, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 2.0, 1)

# error cases for add_item
@pytest.mark.parametrize(
    "unit_price,quantity",
    [(-1, 1), (1, 0), (1, -3), (1, 1.5)],
)
def test_add_item_errors(unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("item", unit_price, quantity)

# remove_item tests
def test_remove_partial(empty_cart):
    empty_cart.add_item("coke", 2.0, 5)
    empty_cart.remove_item("coke", 3)
    assert empty_cart.items() == {"coke": 2}

def test_remove_exact(empty_cart):
    empty_cart.add_item("water", 1.0, 4)
    empty_cart.remove_item("water", 4)
    assert empty_cart.items() == {}

def test_remove_more_than_present(empty_cart):
    empty_cart.add_item("juice", 3.0, 2)
    empty_cart.remove_item("juice", 5)
    assert empty_cart.items() == {}

# removing non-existent raises KeyError
def test_remove_missing_key():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal calculation
@pytest.mark.parametrize(
    "items,expected",
    [
        ([("x", 10.0, 5)], 10.0 * 5 * 0.95),  # 5% discount
        ([("y", 20.0, 12)], 20.0 * 12 * 0.95),
        ([("z", 5.0, 55)], 5.0 * 55 * 0.90),
        ([("w", 1.0, 105)], 1.0 * 105 * 0.85),
    ],
)
def test_subtotal(items, expected):
    c = Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    # round as per spec
    assert round(c.subtotal(), 2) == round(expected, 2)

# total with coupon and shipping
def test_total_no_coupon(empty_cart):
    empty_cart.add_item("item", 100.0, 1)
    assert empty_cart.total() == pytest.approx(160.0)  # 100 + 60 shipping

def test_total_with_member_shipping_discount(empty_cart):
    empty_cart.add_item("item", 200.0, 1)
    # subtotal 200 > free threshold? no, shipping fee 30 for member
    assert empty_cart.total(member=True) == pytest.approx(230.0)

def test_total_with_coupon_and_shipping(empty_cart):
    empty_cart.add_item("item", 300.0, 1)
    # subtotal 300 -> coupon SAVE10 => 270, shipping 60 (subtotal<1000)
    assert empty_cart.total(coupon="SAVE10") == pytest.approx(330.0)

# invalid coupon raises ValueError during total
def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("item", 50.0, 1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")

# empty cart totals to 0 (no shipping)
def test_empty_cart_total():
    c = Cart()
    assert c.total() == 0
