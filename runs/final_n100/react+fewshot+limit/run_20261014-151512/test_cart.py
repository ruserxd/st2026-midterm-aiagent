import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),          # example from spec
    (100.0, 0, 100.0),           # no discount
    (50.5, 100, 0.0),            # full discount
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

# invalid price
with pytest.raises(ValueError):
    apply_discount(-10, 20)

# invalid percent
for bad in (-5, 105, 200):
    with pytest.raises(ValueError):
        apply_discount(100, bad)

# --- bulk_discount_percent ----------------------------------------------
@pytest.mark.parametrize("qty, expected", [
    (9, 0),   # below 10
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

with pytest.raises(ValueError):
    bulk_discount_percent(0)

# --- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

with pytest.raises(ValueError):
    parse_coupon("INVALID")
with pytest.raises(ValueError):
    parse_coupon("SAVE0")   # below 1
with pytest.raises(ValueError):
    parse_coupon("SAVE51")  # above 50

# --- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),
    (750, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    shipping_fee(-10)

# --- Cart class --------------------------------------------------------
@pytest.fixture
def empty_cart():
    return Cart()

# Test adding items

def test_add_item(empty_cart):
    empty_cart.add_item("apple", 2.0, 3)
    assert empty_cart.items() == {"apple": 3}
    # Adding same item increases quantity
    empty_cart.add_item("apple", 2.0, 2)
    assert empty_cart.items() == {"apple": 5}

    with pytest.raises(ValueError):
        empty_cart.add_item("apple", 1.5, 1)  # price mismatch

    with pytest.raises(ValueError):
        empty_cart.add_item("banana", -1, 2)

    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 1, 0)

# Test removing items

def test_remove_item(empty_cart):
    empty_cart.add_item("apple", 2.0, 5)
    empty_cart.remove_item("apple", 3)
    assert empty_cart.items() == {"apple": 2}
    # remove remaining -> item removed
    empty_cart.remove_item("apple", 2)
    assert empty_cart.items() == {}

    with pytest.raises(KeyError):
        empty_cart.remove_item("pear", 1)

# Test subtotal calculation with bulk discount

def test_subtotal_bulk(empty_cart):
    empty_cart.add_item("widget", 10.0, 9)   # no discount
    assert empty_cart.subtotal() == 90.00
    empty_cart.remove_item("widget", 4)
    assert empty_cart.items() == {"widget":5}
    # 5 items -> still no bulk
    assert empty_cart.subtotal() == 50.00
    empty_cart.add_item("widget", 10.0, 5)   # total now 10 items -> 5% discount
    expected = round(10 * 10.0 * (1 - 0.05), 2)
    assert empty_cart.subtotal() == expected

# Test total with coupon and shipping

def test_total_with_coupon_and_shipping(empty_cart):
    # Add one item: price 100, qty 10 -> subtotal after bulk = 950.0
    empty_cart.add_item("gadget", 100.0, 10)
    assert empty_cart.subtotal() == 950.0
    total_no_coupon = empty_cart.total(member=False, coupon=None)
    # shipping: subtotal <1000 => 60
    assert round(total_no_coupon, 2) == round(950.0 + 60.0, 2)

    # with coupon SAVE20 (20% off after bulk)
    total_with_coupon = empty_cart.total(member=False, coupon="SAVE20")
    discounted = 950.0 * 0.80  # 20% off
    expected_total = round(discounted + 60.0, 2)
    assert round(total_with_coupon, 2) == expected_total

    # member gets half shipping
    total_member = empty_cart.total(member=True, coupon=None)
    expected_member_total = round(950.0 + 30.0, 2)
    assert round(total_member, 2) == expected_member_total

# Test total on empty cart is zero (no shipping)
def test_empty_cart_total():
    c = Cart()
    assert c.total() == 0

# Test invalid coupon in total raises ValueError

def test_invalid_coupon_in_total(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")
