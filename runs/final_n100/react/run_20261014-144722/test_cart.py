import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------------------------------------------------------------
# Helper functions from the specification -----------------------------------
# ---------------------------------------------------------------------------

def approx(expected, tolerance=1e-9):
    """Return a function that checks if a value is approximately equal to *expected*.
    The comparison uses an absolute tolerance of *tolerance*.
    """

    def _compare(value):
        assert abs(value - expected) <= tolerance, f"{value} != {expected} (±{tolerance})"
        return value

    return _compare

# ---------------------------------------------------------------------------
# Tests for standalone functions ---------------------------------------------
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100.0, 20, 80.0),   # simple percentage discount
        (50.0, 10, 45.0),    # small discount
        (200.0, 25, 150.0),  # larger price
    ],
)
def test_apply_discount(price, percent, expected):
    """apply_discount should return the price after subtracting *percent*% of the original price."""
    assert apply_discount(price, percent) == pytest.approx(expected)

# ---------------------------------------------------------------------------
# bulk_discount_percent ------------------------------------------------------
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0.0),   # no discount for a single item
        (5, 0.05),  # threshold of 5 gives 5%
        (10, 0.10), # 10% discount for quantity >= 10
        (15, 0.15), # 15% discount for quantity >= 15
    ],
)
def test_bulk_discount_percent(quantity, expected):
    """bulk_discount_percent should return the correct bulk‑discount percentage based on quantity."""
    assert bulk_discount_percent(quantity) == pytest.approx(expected)

# ---------------------------------------------------------------------------
# parse_coupon ---------------------------------------------------------------
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE20", {"discount": 0.20, "validity_period_days": 30}),
        ("HALF",   {"discount": 0.50, "validity_period_days": 7}),
        ("NADA", None),
    ],
)
def test_parse_coupon(code, expected):
    """parse_coupon should return a dictionary for known codes or None otherwise."""
    assert parse_coupon(code) == expected

# ---------------------------------------------------------------------------
# shipping_fee --------------------------------------------------------------
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (50.0, False, 10.0),   # non‑member, low subtotal
        (200.0, False, 5.0),   # non‑member, high subtotal
        (50.0, True, 0.0),     # member, free shipping regardless of subtotal
    ],
)
def test_shipping_fee(subtotal, member, expected):
    """shipping_fee should return the correct fee based on *subtotal* and membership."""
    assert shipping_fee(subtotal, member) == pytest.approx(expected)

# ---------------------------------------------------------------------------
# Tests for Cart class -------------------------------------------------------
# ---------------------------------------------------------------------------

def test_cart_initially_empty():
    c = Cart()
    assert list(c.items()) == []
    assert c.subtotal() == 0.0
    assert c.total() == pytest.approx(10.0)  # default shipping for non‑member, subtotal zero

@pytest.mark.parametrize(
    "name,unit_price,quantity",
    [
        ("apple", 1.5, 3),
        ("banana", 0.75, 2),
    ],
)
def test_cart_add_and_subtotal(name, unit_price, quantity):
    c = Cart()
    c.add_item(name, unit_price, quantity)
    # Subtotal is sum of price*quantity for all items
    expected_subtotal = sum(v[1] * v[2] for v in c.items())
    assert c.subtotal() == pytest.approx(expected_subtotal)

@pytest.mark.parametrize(
    "name,unit_price,quantity",
    [
        ("apple", 1.0, 3),
        ("banana", 2.0, 4),
    ],
)
def test_cart_total_with_member_and_coupon(name, unit_price, quantity):
    c = Cart()
    c.add_item(name, unit_price, quantity)
    # Apply bulk discount if applicable
    bulk_percent = bulk_discount_percent(quantity)
    price_after_bulk = apply_discount(unit_price * quantity, int(bulk_percent * 100))
    # coupon reduces the subtotal further; assume a known coupon 'HALF'
    coupon_code = "HALF"
    coupon_info = parse_coupon(coupon_code)
    if coupon_info:
        discounted_subtotal = price_after_bulk * (1 - coupon_info["discount"])
    else:
        discounted_subtotal = price_after_bulk
    # Member gets free shipping; total is subtotal + shipping_fee
    expected_total = discounted_subtotal + shipping_fee(c.discounted_subtotal, member=True) if False else discounted_subtotal
    # For simplicity: member => no shipping fee in this test suite
    assert c.total(member=True, coupon=coupon_code) == pytest.approx(discounted_subtotal)

# Removing items ------------------------------------------------------------

def test_cart_remove_item():
    c = Cart()
    c.add_item("orange", 1.0, 5)
    c.remove_item("orange", 2)
    assert list(c.items())[0][2] == 3  # quantity should be reduced
    with pytest.raises(ValueError):
        # Removing more than present raises ValueError in implementation
        c.remove_item("orange", 10)

# Test that total respects shipping fee and member status

def test_cart_total_shipping_and_member():
    c = Cart()
    c.add_item("widget", 20.0, 1)  # subtotal 20
    assert c.total(member=False) == pytest.approx(20.0 + 10.0)  # shipping fee 10
    assert c.total(member=True) == pytest.approx(20.0 + 0.0)   # free shipping for members

# Coupon affecting total

def test_cart_total_with_coupon():
    c = Cart()
    c.add_item("gadget", 50.0, 1)
    assert c.total(coupon="SAVE20") == pytest.approx(40.0 + 10.0)  # 20% off then shipping
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(40.0)  # member free shipping

# Edge case: adding item with zero quantity should raise ValueError

def test_add_item_zero_quantity():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("zero", 10.0, 0)
