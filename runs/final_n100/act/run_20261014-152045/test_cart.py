import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Spec helper functions ----------

# Expected discount values based on spec examples
EXAMPLE_APPLY_DISCOUNT = {
    (200, 15): 170.0,
    (100, 0): 100.0,
    (50, 100): 0.0,
}

# ---------- apply_discount tests ----------

@pytest.mark.parametrize("price,percent,expected", [
    (*k, v) for k, v in EXAMPLE_APPLY_DISCOUNT.items()
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

# Boundary values and error cases
@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
# Assume spec: returns a discount percentage based on quantity.
# Since specification is missing implementation details, we deduce common logic:
# - 0-9 items: 0%
# - 10-19 items: 5%
# - 20+ items: 10%

EXPECTED_BULK_DISCOUNTS = {
    1: 0,
    9: 0,
    10: 5,
    15: 5,
    20: 10,
    50: 10,
}

@pytest.mark.parametrize("qty,expected", list(EXPECTED_BULK_DISCOUNTS.items()))
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

# Negative or zero quantity should raise ValueError
@pytest.mark.parametrize("qty", [-1, 0])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------
# Spec states: coupon string may start with 'DISCOUNT' and contains a numeric value.
# Example: "DISCOUNT10" => 0.10 discount (i.e., 10%).

@pytest.mark.parametrize("code,expected", [
    ('DISCOUNT10', 0.10),
    ('DISCOUNT15', 0.15),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# Invalid format or non-numeric should raise ValueError
@pytest.mark.parametrize("code", [
    'DISCOUNTA',
    '10DISCOUNT',
    'discount5',
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
# Spec: free for subtotal >= 100, otherwise flat fee of 20.
# Member status reduces fee by half (rounded down to nearest int).

@pytest.mark.parametrize("subtotal,member,expected", [
    (50, False, 20),
    (150, False, 0),
    (80, True, 10),  # member gets half fee
    (120, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# ---------- Cart class tests ----------

@pytest.fixture
def cart():
    return Cart()

# Test adding items and total calculation with discounts

def test_cart_add_and_subtotal(cart):
    cart.add_item('apple', 1.00, quantity=5)   # subtotal 5.00
    cart.add_item('banana', 0.50, quantity=10)  # subtotal 5.00 more -> total 10.00
    assert cart.subtotal() == 10.00

# Bulk discount applied when items exceed threshold

def test_cart_bulk_discount(cart):
    # Add 20 oranges at $1 each => bulk discount should apply
    cart.add_item('orange', 1.0, quantity=20)
    assert bulk_discount_percent(20) == 10
    # Expected total after applying 10% discount to subtotal
    expected_subtotal = 20 * 1.0
    expected_total_after_bulk = expected_subtotal * (1 - 0.10)
    # Cart.total should apply bulk discount first, then shipping and coupons
    assert cart.total() == pytest.approx(expected_total_after_bulk + shipping_fee(expected_total_after_bulk))

# Test coupon application

def test_cart_coupon(cart):
    cart.add_item('book', 30.0)
    # Apply a 20% coupon
    total_with_coupon = cart.total(coupon='DISCOUNT20')
    expected = apply_discount(30.0, 20) + shipping_fee(apply_discount(30.0, 20))
    assert total_with_coupon == pytest.approx(expected)

# Test member discount on shipping

def test_cart_member_shipping(cart):
    cart.add_item('pen', 5.0)
    subtotal = 5.0
    # Member gets half fee if not free
    expected_fee = shipping_fee(subtotal, member=True)
    assert cart.total(member=True) == pytest.approx(subtotal + expected_fee)

# Test removing items

def test_cart_remove_item(cart):
    cart.add_item('paper', 2.0, quantity=3)
    cart.remove_item('paper', quantity=1)
    assert cart.items()['paper'] == {'unit_price': 2.0, 'quantity': 2}
    # Removing more than present should remove item entirely
    cart.remove_item('paper', quantity=5)
    assert 'paper' not in cart.items()
