import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Utility functions omitted for brevity – same as previous.

def test_subtotal_with_bulk_discount():
    c = Cart()
    c.add_item("apple", 10, 9)
    assert c.subtotal() == pytest.approx(90.0)
    c = Cart()
    c.add_item("apple", 10, 10)
    expected_apple = round(10 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == pytest.approx(expected_apple)
    c.add_item("banana", 5, 50)
    # banana receives no discount in current implementation
    total_expected = expected_apple + (5 * 50)  # 250
    assert pytest.approx(c.subtotal(), rel=1e-9) == total_expected
