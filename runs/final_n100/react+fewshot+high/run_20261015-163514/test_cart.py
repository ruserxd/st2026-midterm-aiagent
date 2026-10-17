# Updated test_cart.py (only the failing parts fixed)
import pytest
import cart

# ---------------------------------------------------------------------
# Bulk discount tests – spec says quantity >= 50 gives 10%, not > 50.
# The implementation mistakenly uses "quantity > 50".
# We keep the spec‑based expected value and will note the mismatch later.
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),   # Spec expects 10
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# ---------------------------------------------------------------------
# parse_coupon – the implementation is case‑sensitive; spec requires case‑insensitive.
# The tests exercise valid coupons with varying cases to expose this bug.
# ---------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),   # Should be accepted but fails
        (" SAVE30 ", 30),
        ("SaVe15", 15),   # Case‑insensitive expected but implementation requires uppercase.
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# ---------------------------------------------------------------------
# subtotal – spec says bulk discount applied to each item before summing.
# Implementation seems correct but our calculations earlier gave 235.0 vs expected 225.0.
# This indicates the implementation may be applying the bulk discount incorrectly.
# We'll keep the spec‑based expectation and note the mismatch.
# ---------------------------------------------------------------------
class TestCart:
    def setup_method(self, method):
        self.c = cart.Cart()

    def test_subtotal_with_bulk_discounts(self):
        # Stick: 5.0 * 9, no discount
        stick_total = round(5.0 * 9, 2)
        # Box: 10.0 * 20 with 10% bulk discount
        box_total = round(10.0 * 20 * (1 - 0.10), 2)
        expected = round(stick_total + box_total, 2)  # spec expects 225.0
        assert self.c.subtotal() == expected
+
*** End of file ***
