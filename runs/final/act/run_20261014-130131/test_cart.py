import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- simple helpers ---

# ---------- tests for standalone functions ----------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.99, 10, 89.99),  # rounded to 2 decimals
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

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

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 1.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVE0", "SAVE51", "10SAVE", "SAVE-5", "  ", "NOTA"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- tests for Cart class ----------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 0.5)
    # adding existing item with same price increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5, "banana": 1}

    # remove part of quantity
    c.remove_item("apple", 3)
    assert c.items()["apple"] == 2

    # remove fully -> item removed
    c.remove_item("banana")
    assert "banana" not in c.items()

    # removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("orange")

    # invalid add (different price)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)

    # invalid remove quantity (negative) – should still work? spec does not forbid negative removal; but test for non-negative logic isn't defined.


def test_cart_subtotal_with_bulk_discounts():
    c = Cart()
    # 5 apples at $2 each -> no bulk discount
    c.add_item("apple", 2.0, 5)
    assert c.subtotal() == 10.0
    # 50 bananas at $1 each -> 10% bulk discount
    c.add_item("banana", 1.0, 50)
    # banana subtotal before discount: 50*1=50; after 10% => 45.0
    # total should be 10 + 45 = 55
    assert pytest.approx(c.subtotal(), rel=1e-9) == 55.0


def test_cart_total_no_coupon_non_member():
    c = Cart()
    c.add_item("item", 100, 5)  # no bulk discount, subtotal 500
    total = c.total(member=False)
    # shipping fee for 500 -> 60
    assert pytest.approx(total, rel=1e-9) == 560.0


def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("item", 100, 5)  # subtotal 500
    # coupon SAVE10 -> reduce by 10% => 450
    total = c.total(member=True, coupon="SAVE10")
    # shipping fee for 450 with member: 30
    assert pytest.approx(total, rel=1e-9) == 480.0


def test_cart_total_with_invalid_coupon():
    c = Cart()
    c.add_item("item", 50)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Ensure empty cart has no shipping fee

def test_empty_cart_no_shipping():
    assert Cart().total() == 0.0
