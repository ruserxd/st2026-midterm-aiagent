import pytest
from cart import Cart, parse_coupon, bulk_discount_percent, shipping_fee, apply_discount

# Utility fixtures for common carts
def empty_cart():
    return Cart()

@pytest.fixture
def simple_cart():
    c = Cart()
    c.add_item("apple", 1.0, quantity=2)
    c.add_item("banana", 0.5)
    return c

# 1. Subtotal calculations

def test_subtotal_empty_cart(empty_cart):
    assert empty_cart.subtotal() == 0

def test_subtotal_simple(simple_cart):
    # 2 apples * $1 + 1 banana * $0.5 = $2.5
    assert simple_cart.subtotal() == 2.5

# 2. Bulk discount percentage function

def test_bulk_discount_percent():
    # No bulk for quantity <=10
    assert bulk_discount_percent(5) == 0
    # Bulk discount applies at 20 items
    assert bulk_discount_percent(20) == 5
    # Ensure monotonicity: higher qty same or higher percent
    assert bulk_discount_percent(25) >= bulk_discount_percent(20)

# 3. Shipping fee function

def test_shipping_fee_zero_subtotal():
    assert shipping_fee(0, member=False) == 0
    assert shipping_fee(0, member=True) == 0

def test_shipping_fee_non_member():
    # For subtotal $50, flat $10 fee
    assert shipping_fee(50) == 10
    # Above $100 no fee
    assert shipping_fee(150) == 0

def test_shipping_fee_member():
    # Member: no fee up to $200
    assert shipping_fee(199.99, member=True) == 0
    # Beyond $200, $5 fee
    assert shipping_fee(250, member=True) == 5

# 4. Coupon parsing

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("20OFF") == 20

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        parse_coupon("INVALIDCODE")

# 5. Total calculation without coupon or membership

def test_total_no_coupon_or_member(simple_cart):
    # subtotal $2.5, shipping fee for non-member: $10 (subtotal <100)
    expected = round(2.5 + 10, 2)
    assert simple_cart.total() == expected

# 6. Total with member discount and coupon

def test_total_member_and_coupon(simple_cart):
    # subtotal $2.5, apply 10% coupon => $2.25
    # shipping for members up to $200: still $0 (since <200)
    expected = round(2.25 + 0, 2)
    assert simple_cart.total(member=True, coupon="SAVE10") == expected

# 7. Empty cart total

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0

# 8. Coupon edge cases: rounding behavior

def test_coupon_rounding(simple_cart):
    # Use a coupon that leads to fractional cents
    # subtotal $2.5, 33% off -> 1.6666...
    expected = round(1.6666667 + shipping_fee(1.6666667), 2)
    assert simple_cart.total(coupon="333") == expected
