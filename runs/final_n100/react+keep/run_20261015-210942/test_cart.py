import pytest
import cart

# ---- Helper functions for expected values from spec ----

def apply_discount_spec(price, percent):
    if price < 0:
        raise ValueError("price must be >= 0")
    if not (0 <= percent <= 100):
        raise ValueError("percent out of range")
    return round(price * (1 - percent / 100), 2)

# ----- tests for standalone functions ----

@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (50, 0, 50.0),
        (100, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (10, -5), (10, 150)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests

@ pytest.mark.parametrize(
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
    assert cart.bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize(
    "quantity",
    [0, -5, 1.2],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests

@ pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE25 ", 25),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@ pytest.mark.parametrize(
    "code",
    ["SAVEXY", "save0", "SAVE101", "ABCD10", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests

@ pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, False, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class tests ----

@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple": 3}
    assert empty_cart.subtotal() == 3.0  # no bulk discount yet

def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana", 2.5, 2)
    empty_cart.add_item("banana", 2.5, 1)
    assert empty_cart.items() == {"banana": 3}
    # bulk discount applies: qty=3 <10 => 0%
    assert empty_cart.subtotal() == 7.5

def test_add_item_existing_different_price(empty_cart):
    empty_cart.add_item("orange", 1.2, 2)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.3, 1)

@pytest.mark.parametrize(
    "quantity",
    [0, -5],
)
def test_add_item_invalid_quantity(empty_cart, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 1.0, quantity)

def test_remove_item_partial(empty_cart):
    empty_cart.add_item("mango", 3.0, 5)
    empty_cart.remove_item("mango", 2)
    assert empty_cart.items() == {"mango": 3}
    # subtotal still affected by bulk discount for qty=3
    assert empty_cart.subtotal() == 9.0

def test_remove_item_complete(empty_cart):
    empty_cart.add_item("kiwi", 4.0, 2)
    empty_cart.remove_item("kiwi", 2)
    assert "kiwi" not in empty_cart.items()

def test_remove_item_not_in_cart():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal bulk discount testing

def test_subtotal_bulk_discount(empty_cart):
    # 12 apples -> 5% discount on each
    empty_cart.add_item("apple", 10.0, 12)  # 120 raw
    assert round(empty_cart.subtotal(), 2) == round(120 * (1-0.05), 2)

# total calculation tests

def test_total_with_coupon_and_shipping(empty_cart):
    empty_cart.add_item("book", 200.0, 5)  # raw subtotal 1000, bulk discount 0%
    # coupon SAVE10 => 10% off subtotal -> 900
    # shipping fee for members: half of 60 = 30 (since subtotal < 1000)
    total = empty_cart.total(member=True, coupon="SAVE10")
    assert round(total, 2) == round(900 + 30, 2)

def test_total_without_coupon_no_shipping(empty_cart):
    # subtotal exactly 1000 -> free shipping
    empty_cart.add_item("expensive", 500.0, 2)  # raw 1000
    assert empty_cart.total() == 1000.0

# total with invalid coupon

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("toy", 50.0, 1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="invalid")

# total on empty cart

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
