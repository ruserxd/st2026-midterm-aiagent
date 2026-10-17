import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent, apply_discount

# Helper for rounding comparison
def round2(x):
    return round(float(x), 2)

class TestCartTotal:
    def test_empty_cart(self):
        c = Cart()
        assert round2(c.total()) == 0.00

    def test_simple_item_no_coupon(self):
        c = Cart()
        c.add_item("apple", unit_price=1.50, quantity=3)
        expected_subtotal = 4.50
        expected_shipping = shipping_fee(expected_subtotal)
        assert round2(c.total()) == round2(expected_subtotal + expected_shipping)

    def test_coupon_applied(self):
        c = Cart()
        c.add_item("banana", unit_price=2.00, quantity=5)
        # subtotal is 10.0, coupon 20% gives 8.0, then shipping on 8.0
        expected_total = round2(8.0 + shipping_fee(8.0))
        assert round2(c.total(coupon="SAVE20")) == expected_total

    def test_invalid_coupon_raises(self):
        c = Cart()
        c.add_item("item", 1, 1)
        with pytest.raises(ValueError):
            c.total(coupon="INVALID")

    def test_member_discount_applied_to_shipping(self):
        # member flag influences shipping fee; assume shipping_fee subtracts $5 for members
        c = Cart()
        c.add_item("widget", 10.0, quantity=1)
        subtotal = 10.0
        expected_total_no_member = round2(subtotal + shipping_fee(subtotal))
        expected_total_member = round2(subtotal + shipping_fee(subtotal, member=True))
        assert round2(c.total(member=False)) == expected_total_no_member
        assert round2(c.total(member=True)) == expected_total_member

class TestUtilityFunctions:
    def test_bulk_discount_percent(self):
        # quantity thresholds from spec
        assert bulk_discount_percent(9) == 0
        assert bulk_discount_percent(10) == 5
        assert bulk_discount_percent(20) == 5
        assert bulk_discount_percent(50) == 10
        assert bulk_discount_percent(100) == 15

    def test_apply_discount_rounding(self):
        # apply_discount(price, percent)
        assert round2(apply_discount(100.0, 15)) == 85.00
        assert round2(apply_discount(55.5, 25)) == 41.62

    def test_parse_coupon_valid_and_invalid(self):
        assert parse_coupon("SAVE20") == 20
        with pytest.raises(ValueError):
            parse_coupon("UNKNOWN")
