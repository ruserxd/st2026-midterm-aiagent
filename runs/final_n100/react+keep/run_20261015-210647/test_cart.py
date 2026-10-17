import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# --- Test apply_discount ---

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
    (99.99, 10, 89.99)         # rounding test: 99.99 * 0.9 = 89.991 => rounded to 89.99
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-10, 5), (10, -1), (10, 101)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --- Test bulk_discount_percent ---

@pytest.mark.parametrize("quantity,expected", [
    (1, 0),            # less than 5 items: no discount
    (4, 0),            # exactly 4: still no discount
    (5, 5),            # 5-9 items => 5%
    (7, 5),            # within same tier
    (10, 10),          # 10-19 items => 10%
    (25, 15),          # 20+ items => 15%
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# --- Test parse_coupon ---

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", ("SAVE10", 10)),          # valid code
    ("50OFF", ("50OFF", 50)),            # max 50% discount allowed
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "INVALID",          # does not match pattern
    "SAVE-10",           # hyphen not allowed
    "ABCD12345",         # more than 5 chars before number
    "SVE9",              # less than 4 chars
    "SAVE101",           # percent > 100
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- Test shipping_fee ---

@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 5.0),            # zero subtotal, not member => base fee
    (10, False, 3.0),           # subtotal < $50
    (49.99, False, 3.0),        # just below threshold
    (50, False, 0.0),           # free for members
    (51, True, 0.0),            # member with any subtotal => free
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# --- Test Cart class functionality ---

@pytest.fixture
def empty_cart():
    return Cart()

def test_add_and_items(empty_cart):
    cart = empty_cart
    cart.add_item("Apple", 1.0)
    assert cart.items() == {"Apple": (1.0, 1)}
    cart.add_item("Banana", 0.5, quantity=3)
    assert cart.items()["Banana"] == (0.5, 3)

def test_remove_item(empty_cart):
    cart = empty_cart
    cart.add_item("Apple", 1.0, quantity=5)
    cart.remove_item("Apple")  # default remove one
    assert cart.items()["Apple"] == (1.0, 4)
    cart.remove_item("Apple", quantity=3)
    assert "Apple" not in cart.items()

def test_subtotal(empty_cart):
    cart = empty_cart
    cart.add_item("Apple", 2.5, quantity=2)  # $5.00
    cart.add_item("Banana", 1.0, quantity=3)  # $3.00
    assert cart.subtotal() == 8.0

# Testing total calculation with member flag and coupon

def test_total_member_and_coupon(empty_cart):
    cart = empty_cart
    cart.add_item("ItemA", 100.0)
    cart.add_item("ItemB", 200.0)
    # subtotal $300, shipping for non-member >$50 => $5
    total_no_discount = cart.total(member=False, coupon=None)
    assert total_no_discount == 305.0
    # member: free shipping, no coupon
    total_member = cart.total(member=True, coupon=None)
    assert total_member == 300.0
    # apply a valid coupon (e.g., "SAVE10") that reduces subtotal by 10%
    total_with_coupon = cart.total(member=False, coupon="SAVE10")
    expected_subtotal = 300 * 0.9
    expected_total = round(expected_subtotal + 5.0, 2)
    assert total_with_coupon == expected_total

# Ensure that total raises ValueError for invalid coupon codes

def test_total_invalid_coupon(empty_cart):
    cart = empty_cart
    cart.add_item("Item", 10.0)
    with pytest.raises(ValueError):
        cart.total(member=False, coupon="INVALID")
