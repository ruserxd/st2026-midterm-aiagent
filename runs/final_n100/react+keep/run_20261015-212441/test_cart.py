import pytest
import cart

# ---------- parse_coupon tests based on specification ----------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [None, 123, [], {}])
def test_parse_coupon_invalid_type(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("code", ["DISCOUNT10", "SAVEXX", "SAVE0", "SAVE51", " SAVE-5 ", "123SAVE10", "SAVEE10"])
def test_parse_coupon_invalid_code(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Cart.total tests following specification ----------

@pytest.fixture
def simple_cart():
    c = cart.Cart()
    # Add a single item costing 200.00 dollars
    c.add_item("Widget", 200.0, quantity=3)  # subtotal 600.0
    return c

# Helper: calculate shipping based on discounted amount (expected behaviour)

def expected_shipping(discounted_subtotal, member):
    if discounted_subtotal >= 1000:
        return 0
    fee = 60
    return fee / 2 if member else fee

def test_total_empty_cart():
    empty = cart.Cart()
    assert empty.total() == 0

# Test without coupon, non-member

def test_total_no_coupon_non_member(simple_cart):
    subtotal = simple_cart.subtotal()
    expected = round(subtotal + expected_shipping(subtotal, member=False), 2)
    assert simple_cart.total() == expected

# Test with coupon affecting discount and shipping calculation

def test_total_with_coupon_discounts_and_ships(simple_cart):
    # Apply a 20% coupon
    subtotal_before = simple_cart.subtotal()
    discounted = round(subtotal_before * (1 - 0.20), 2)
    expected_shipping_fee = expected_shipping(discounted, member=False)
    total_expected = round(discounted + expected_shipping_fee, 2)
    assert simple_cart.total(coupon="SAVE20") == pytest.approx(total_expected)

# Test member shipping discount

def test_total_member_shipping(simple_cart):
    subtotal = simple_cart.subtotal()
    expected = round(subtotal + expected_shipping(subtotal, member=True), 2)
    assert simple_cart.total(member=True) == expected

# Verify that the implementation incorrectly uses original subtotal for shipping fee
# This test will fail if the bug is present (shipping fee based on non-discounted subtotal)

def test_bugged_shipping_fee_behavior(simple_cart):
    # With a large discount, discounted subtotal < FREE_SHIPPING_THRESHOLD
    # but the original subtotal may be > threshold, causing shipping to incorrectly be free.
    # For example, add expensive items to push subtotal above 1000.
    big_cart = cart.Cart()
    big_cart.add_item("Expensive", 1200.0)
    # Now apply a coupon that reduces below threshold
    assert big_cart.total(coupon="SAVE50") == pytest.approx(round(600 + expected_shipping(600, False), 2))

# The above test demonstrates the discrepancy: if shipping_fee used discounted subtotal,
# the total should be rounded to 600 + 60 = 660.0. If the buggy implementation uses original
# subtotal for shipping (free fee), the total would be 600.0.
