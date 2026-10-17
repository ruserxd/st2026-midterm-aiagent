import pytest
from cart import Cart, parse_coupon, shipping_fee

# Helper to build a cart with given items: (name, price, qty)

def build_cart(items):
    c = Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

@pytest.mark.parametrize(
    "items, coupon, member, expected_total",
    [
        # Empty cart -> 0 cost
        ([], None, False, 0.00),
        ([], None, True, 0.00),
        # Simple case: subtotal less than shipping threshold, no coupon
        ([("apple", 1.50, 2)], None, False, 63.00),  # subtotal 3 + shipping 60
        # Same with member discount on shipping (30)
        ([("apple", 1.50, 2)], None, True, 33.00),
        # Coupon applied: discount before shipping
        ([("banana", 2.00, 5)], "SAVE10", False, round(9.00 + 60.0, 2)),  # subtotal 10 -> 9 after 10% -> +60 = 69.00
        # Coupon with member: shipping half
        ([("banana", 2.00, 5)], "SAVE20", True, round(8.00 + 30.0, 2)),
    ],
)
def test_total_behavior(items, coupon, member, expected_total):
    cart = build_cart(items)
    total = cart.total(member=member, coupon=coupon)
    assert total == expected_total

# Test that an invalid coupon raises ValueError

def test_invalid_coupon():
    c = Cart()
    c.add_item("orange", 1.00, 3)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Test shipping fee directly for clarity

def test_shipping_fee_cases():
    assert shipping_fee(0) == 60
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500, member=True) == 0
    assert shipping_fee(50, member=True) == 30
