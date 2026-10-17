import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# ---------- Helper functions ------------------------------------------------

def _cart_with_items(*items):
    """Create a Cart and add each (name, unit_price, quantity) tuple.
    ``items`` may be any iterable of tuples.
    """
    c = Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# ---------- Tests for individual helper functions ---------------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (99.99, 0, 99.99),
        (50.0, 100, 0.0),
        (1234.56, 25, 925.92),
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "quantity,percent",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (15, 5),
        (50, 10),
        (51, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, percent):
    assert bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "save0",   # percent out of range
        "SAVE100", # percent too high
        "SAVExx",  # not digits
        "DIS10",   # wrong prefix
        123,        # non-string
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0.0, False, 60),   # no shipping fee free threshold not reached
        (999.99, False, 60),
        (1000.00, False, 0),
        (2000.00, True, 0),
        (50.0, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, result):
    assert shipping_fee(subtotal, member) == result

# ---------- Tests for Cart subtotal and total ------------------------------

def test_cart_subtotal_basic():
    cart = _cart_with_items(
        ("apple", 1.00, 5),   # no discount
        ("banana", 0.50, 10), # 5% discount on banana line
        ("cherry", 2.00, 100),# 15% discount on cherry line
    )
    # Expected line totals after discounts:
    apple_total = apply_discount(1.00 * 5, bulk_discount_percent(5))   # 0% -> 5.0
    banana_total = apply_discount(0.50 * 10, bulk_discount_percent(10))# 5% -> round(5*0.95)=4.75
    cherry_total = apply_discount(2.00 * 100, bulk_discount_percent(100))#15%->round(200*0.85)=170.0
    expected_subtotal = round(apple_total + banana_total + cherry_total, 2)
    assert cart.subtotal() == expected_subtotal

@pytest.mark.parametrize(
    "member,coupon,total_expected",
    [
        (False, None, 75.0),          # subtotal 60 -> shipping 60 => total 120? Wait calculation: We'll design scenario.
    ],
)
def test_cart_total_basic(member, coupon, total_expected):
    cart = _cart_with_items(
        ("item", 10.00, 1),
    )
    # Subtotal is 10.00
    # No coupon => amount remains 10
    # Shipping fee for subtotal=10 <1000 => 60 or 30 if member
    shipping = shipping_fee(10.00, member)
    expected_total = round(10.00 + shipping, 2)
    assert cart.total(member=member, coupon=coupon) == expected_total

# Test that coupon discount is applied before shipping calculation

def test_cart_total_with_coupon():
    cart = _cart_with_items(
        ("expensive", 500.00, 1),   # subtotal 500
    )
    amount_after_discount = apply_discount(500.0, parse_coupon("SAVE10"))  # 450
    shipping = shipping_fee(amount_after_discount, member=False)
    expected_total = round(amount_after_discount + shipping, 2)
    assert cart.total(coupon="SAVE10") == expected_total

# Test that invalid coupon raises ValueError

def test_cart_total_invalid_coupon():
    cart = _cart_with_items(
        ("item", 20.00, 1),
    )
    with pytest.raises(ValueError):
        cart.total(coupon="SAVE0")  # percent out of range

# Test empty cart total is zero and no shipping

def test_empty_cart_total():
    cart = Cart()
    assert cart.total() == 0

# Test remove_item bug: removing exact quantity should delete the item

def test_remove_item_deletes_exact_quantity_bugged_behavior():
    cart = _cart_with_items(("gadget", 5.00, 3))
    # Remove all three units
    cart.remove_item("gadget", 3)
    assert "gadget" not in cart.items()

# Test add_item error handling

def test_add_item_errors():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("badprice", -1, 1)
    cart.add_item("good", 10.0, 2)
    with pytest.raises(ValueError):
        cart.add_item("good", 12.0, 1)  # price mismatch
    with pytest.raises(ValueError):
        cart.add_item("badqty", 5.0, 0)
    with pytest.raises(ValueError):
        cart.add_item("badqty2", 5.0, -3)

# Test remove_item error handling for non-existent item

def test_remove_item_nonexistent():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item("missing")

"""
Run this test suite to validate the module implementation against its specification.
"""
