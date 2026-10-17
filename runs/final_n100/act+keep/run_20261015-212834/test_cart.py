import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Helper for approximate equality due to rounding

def approx_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ------------------- apply_discount tests -------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-12)

@pytest.mark.parametrize(
    "price,percent",
    [
        (-10, 10),                 # negative price
        (100, -5),                 # negative percent
        (100, 105),                # percent > 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ------------------- bulk_discount_percent tests -------------------

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),     # below threshold
        (10, 5),    # first tier
        (49, 5),    # just below second tier
        (50, 10),   # second tier
        (99, 10),   # just below third tier
        (100, 15),  # third tier and above
        (500, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.14],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ------------------- parse_coupon tests -------------------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe5  ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",      # percent <1
        "SAVE51",     # >50
        "SAVExx",     # non numeric
        "DISCOUNT10",  # wrong prefix
        "12345",       # no prefix
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ------------------- shipping_fee tests -------------------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),   # below threshold
        (1000, True, 0),       # free
        (1200, False, 0),      # free
        (200, True, 30),       # member half fee
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ------------------- Cart tests -------------------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0

# Adding items and checking subtotal with bulk discounts

def test_add_and_subtotal():
    cart = Cart()
    # Add 5 units of apple at $20 each (no bulk discount)
    cart.add_item("apple", 20, 5)
    assert cart.subtotal() == pytest.approx(100.0)
    # Add 10 more apples, total quantity 15 -> bulk discount 5%
    cart.add_item("apple", 20, 10)
    # subtotal calculation: (30 units * $20) = 600
    # bulk discount percent for 30? Since quantity=30 => 5% per spec.
    expected_before_discount = 600.0
    discounted = apply_discount(expected_before_discount, 5)
    assert cart.subtotal() == pytest.approx(discounted)

# Removing items and verifying removal when zero

def test_remove_items():
    cart = Cart()
    cart.add_item("banana", 1.5, 3)
    cart.remove_item("banana", 2)
    assert cart.items() == {"banana": 1}
    cart.remove_item("banana", 1)
    assert cart.items() == {}

# Removing non-existent item raises KeyError

def test_remove_nonexistent():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item("orange", 1)

# Adding same item with different price raises ValueError

def test_add_same_name_different_price():
    cart = Cart()
    cart.add_item("grape", 0.5, 10)
    with pytest.raises(ValueError):
        cart.add_item("grape", 0.75, 5)

# Total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("widget", 100, 12)  # quantity 12 -> bulk discount 5%
    subtotal_before_coupon = cart.subtotal()
    # Apply coupon SAVE10 (10%)
    amount_after_coupon = apply_discount(subtotal_before_coupon, 10)
    expected_total = round(amount_after_coupon + shipping_fee(amount_after_coupon), 2)
    assert cart.total(coupon="SAVE10") == pytest.approx(expected_total)

# Total with member discount on shipping only (no coupon)

def test_total_member_shipping():
    cart = Cart()
    cart.add_item("thing", 200, 1)  # no bulk discount
    subtotal = cart.subtotal()
    expected_total = round(subtotal + shipping_fee(subtotal, member=True), 2)
    assert cart.total(member=True) == pytest.approx(expected_total)

# Total for empty cart is zero (no shipping)

def test_empty_cart_total_zero_shipping():
    cart = Cart()
    assert cart.total() == 0.0

# Coupon case-insensitivity and whitespace handling

def test_coupon_whitespace_and_case_insensitive():
    cart = Cart()
    cart.add_item("item", 10, 1)
    # Using mixed case and surrounding spaces should still work
    assert cart.total(coupon="  SaVe5 ") == pytest.approx(
        round(cart.subtotal() + shipping_fee(cart.subtotal()), 2)
    )
