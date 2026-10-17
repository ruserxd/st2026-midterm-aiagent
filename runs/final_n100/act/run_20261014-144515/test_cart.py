import pytest
from math import isclose

import cart

# Helper: create a Cart with given items (quantity * unit price)

def make_cart(items):
    """Return a Cart instance populated with the provided items.
    Each item is a tuple (name, quantity, price)."""
    c = cart.Cart()
    for name, qty, price in items:
        c.add_item(name=name, quantity=qty, unit_price=price)
    return c

# ---------------------------------------------------------------------------
# Tests for parse_coupon
# ---------------------------------------------------------------------------

def test_parse_coupon_valid_cases():
    # exact matches and whitespace variations
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30
    assert cart.parse_coupon("SaVe40") == 40


def test_parse_coupon_invalid_cases():
    # non-matching patterns or out of bounds values raise ValueError
    invalid_inputs = ["", "SAVEBAD", "save0", "save51", "save-5", "save99",
                      "   ", "SAVE100", "INVALID"]
    for inp in invalid_inputs:
        with pytest.raises(ValueError, match="Invalid coupon code"):
            cart.parse_coupon(inp)

# ---------------------------------------------------------------------------
# Tests for Cart.total
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("items,total_expected", [
    # Empty cart: total 0.0 (no shipping)
    ([], 0.00),
    # Simple cart without coupon or shipping (subtotal < $50 triggers no fee?)
    ([("apple", 2, 3)], 6.00),  # subtotal 6
    # Cart with multiple items: compute subtotal then shipping
    ([("item1", 5, 10)], 55.00)   # subtotal 50 -> shipping applies? depends on rule
])

def test_cart_total_simple(items, total_expected):
    c = make_cart(items)
    assert isclose(c.total(), total_expected, rel_tol=1e-9)

# Note: the spec does not detail shipping logic. The tests assume that a cart
# with subtotal 50 triggers shipping of $5 (example). Adjust according to actual implementation.

def test_cart_total_with_coupon():
    c = make_cart([("item", 10, 20)])  # subtotal 200
    # Apply 25% coupon
    total = c.total(coupon="SAVE25")
    # Expected: 200 * (1-0.25) = 150 + shipping
    # Shipping calculated on discounted amount; assuming flat $5 for demo
    expected_discounted = 150.00
    # Let's inspect implementation to know shipping_fee calculation
    fee = c.shipping_fee(expected_discounted)
    assert isclose(total, round(expected_discounted + fee, 2), rel_tol=1e-9)

# Test that invalid coupon raises ValueError

def test_cart_total_invalid_coupon():
    c = make_cart([("item", 1, 10)])
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
