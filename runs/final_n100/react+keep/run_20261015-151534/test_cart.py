import pytest
import cart

# ---- helper functions to compute expected values based on spec ----

def discounted_subtotal(subtotal, percent):
    """Return subtotal after applying a percentage discount."""
    return subtotal * (1 - percent / 100)


def shipping_fee_expected(subtotal, member=False):
    """Compute shipping fee according to cart.shipping_fee spec.
    Shipping is free for orders >= 1000.
    Base fee is 60; members pay half.
    """
    if subtotal < 0:
        raise ValueError("subtotal must be non-negative")
    if subtotal >= 1000:
        return 0
    fee = 60
    if member:
        fee /= 2
    return fee

# ---- tests for parse_coupon ---------------------------------------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("sAvE45", 45),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "",          # empty string
        "SAVEX",      # non-digit suffix
        "10SAVE",     # digits before prefix
        "SAVE-5",     # negative number
        "SAVE55",     # >50
        "SAVE0",      # <1
        "ABC10",      # wrong prefix
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- tests for Cart.total ------------------------------------------

def make_cart_with_items(*items):
    """Helper to create a cart and add given items.
    Each item is a tuple: (name, unit_price, quantity).
    """
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# Subtotal < 1000, no coupon
@pytest.mark.parametrize(
    "items",
    [
        ([("apple", 50, 2), ("banana", 20, 1)]),   # subtotal = 120
        ([("widget", 999.99, 1)]),                  # subtotal just below threshold
    ],
)
def test_total_no_coupon(items):
    c = make_cart_with_items(*items)
    subtotal = sum(price * qty for _, price, qty in items)
    expected = round(subtotal + shipping_fee_expected(subtotal), 2)
    assert c.total() == expected

# Subtotal < 1000, with valid coupon
@pytest.mark.parametrize(
    "items, coupon, percent",
    [
        ([("apple", 50, 2)], "SAVE10", 10),          # subtotal 100
        ([("widget", 200, 1)], "save20", 20),       # subtotal 200
    ],
)
def test_total_with_coupon(items, coupon, percent):
    c = make_cart_with_items(*items)
    subtotal = sum(price * qty for _, price, qty in items)
    discounted = discounted_subtotal(subtotal, percent)
    expected = round(discounted + shipping_fee_expected(discounted), 2)
    assert c.total(coupon=coupon) == expected

# Invalid coupon raises ValueError
@pytest.mark.parametrize(
    "items, invalid_coupon",
    [
        ([("apple", 50, 2)], "BADCODE"),
        ([("widget", 200, 1)], "SAVE70"),          # >50 discount
    ],
)
def test_total_invalid_coupon(items, invalid_coupon):
    c = make_cart_with_items(*items)
    with pytest.raises(ValueError):
        c.total(coupon=invalid_coupon)

# Test that member flag reduces shipping fee by half (even though spec doesn't mention it)
@pytest.mark.parametrize(
    "items, coupon, percent",
    [
        ([("widget", 200, 1)], None, 0),             # subtotal 200
    ],
)
def test_total_member_shipping(items, coupon, percent):
    c = make_cart_with_items(*items)
    subtotal = sum(price * qty for _, price, qty in items)
    discounted = discounted_subtotal(subtotal, percent)
    expected = round(discounted + shipping_fee_expected(discounted, member=True), 2)
    assert c.total(member=True, coupon=coupon) == expected
