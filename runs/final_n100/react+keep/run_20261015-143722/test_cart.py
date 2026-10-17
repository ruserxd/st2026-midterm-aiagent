import re
import pytest
import cart

# Helper function to compare floats with rounding as per spec

def round2(value):
    return round(float(value), 2)

# ---------------------------------------------------------------------------
# Tests for parse_coupon
# ---------------------------------------------------------------------------

def test_parse_coupon_valid_cases():
    # Test a few valid codes (case-insensitive, whitespace stripped)
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("   SaVe5  ") == 5


def test_parse_coupon_invalid_cases():
    # Codes not matching pattern or out of bounds should raise ValueError
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")          # below minimum
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")         # above maximum
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEXX")        # non-numeric suffix
    with pytest.raises(ValueError):
        cart.parse_coupon(123)              # wrong type

# ---------------------------------------------------------------------------
# Tests for apply_discount
# ---------------------------------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding_and_bounds():
    # Ensure rounding to two decimals
    assert cart.apply_discount(99.999, 10) == round2(99.999 * 0.9)
    # ValueError for negative price
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    # ValueError for percent out of bounds
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------------------------------------------------------------------------
# Tests for bulk_discount_percent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),   # below threshold
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected


def test_bulk_discount_percent_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.14)  # not an int

# ---------------------------------------------------------------------------
# Tests for shipping_fee
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),          # subtotal < 1000, non-member
        (500, True, 30),         # half fee for member
        (999.99, False, 60),
        (1000, False, 0),        # free shipping threshold
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10, False)

# ---------------------------------------------------------------------------
# Tests for Cart class behavior (spec-compliant expectations)
# ---------------------------------------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 100, 2)
    assert c.items() == {"apple": 2}
    # Adding same item increases quantity
    c.add_item("apple", 100, 3)
    assert c.items() == {"apple": 5}
    # Different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 90, 1)


def test_cart_remove_and_zero_quantity():
    c = cart.Cart()
    c.add_item("banana", 50, 5)
    # Remove some quantity
    c.remove_item("banana", 2)
    assert c.items() == {"banana": 3}
    # Removing more than current should delete item
    c.remove_item("banana", 10)  # reduces to -7 and deletes
    assert "banana" not in c.items()
    # Removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("orange")


def test_cart_subtotal_and_bulk_discount():
    c = cart.Cart()
    # 10 apples at $10 each -> bulk discount 5%
    c.add_item("apple", 10, 10)
    expected_line_total = 10 * 10  # unit price times quantity
    discounted = cart.apply_discount(expected_line_total, 5)
    assert round2(discounted) == round2(100 * 0.95)
    assert round2(c.subtotal()) == round2(discounted)


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    # Total with no coupon, non-member: expect shipping fee applied to subtotal
    c.add_item("item", 100, 1)  # subtotal 100
    total_no_coupon = round2(100 + cart.shipping_fee(100, False))
    assert c.total(member=False) == total_no_coupon

    # Add coupon SAVE10: should reduce amount before shipping
    c.add_item("extra", 50, 1)  # subtotal now 150
    amount_after_discount = cart.apply_discount(150, 10)
    expected_total = round2(amount_after_discount + cart.shipping_fee(150, False))
    assert c.total(coupon="SAVE10") == expected_total

    # Member discount: half shipping fee after coupon
    expected_member_total = round2(amount_after_discount + cart.shipping_fee(150, True))
    assert c.total(member=True) == expected_member_total

    # Empty cart returns 0
    empty_cart = cart.Cart()
    assert empty_cart.total() == 0

# ---------------------------------------------------------------------------
# Test to detect implementation bug in total shipping fee calculation
# ---------------------------------------------------------------------------

def test_total_shipping_fee_bug_detection():
    """
    The current implementation incorrectly passes the original subtotal to
    ``shipping_fee`` instead of the discounted amount.  This test checks for
    that bug by creating a scenario where the coupon changes the shipping
    eligibility threshold.
    """
    c = cart.Cart()
    # Subtotal is $1200, free shipping normally. Add a coupon that reduces
    # it below $1000 to trigger shipping fee.
    c.add_item("expensive", 1200, 1)
    assert c.total() == 1200  # no shipping
    # Apply a 20% coupon (SAVE20) which should bring amount to 960
    total_with_coupon = round2(960 + cart.shipping_fee(1200, False))
    # The buggy implementation would still use the original 1200 for shipping,
    # giving 0 shipping fee; hence it would incorrectly return 960.
    assert c.total(coupon="SAVE20") == total_with_coupon
