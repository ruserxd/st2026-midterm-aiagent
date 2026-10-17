import pytest
from cart import Cart, parse_coupon, shipping_fee

# Helper to compute expected subtotal for a list of items

def calc_subtotal(items):
    return sum(unit * qty for _, unit, qty in items)

class TestCart:
    def test_empty_cart_total_is_zero(self):
        c = Cart()
        assert c.total() == 0.00

    def test_total_without_coupon_and_non_member(self):
        c = Cart()
        items = [("apple", 1.00, 2), ("banana", 0.50, 4)]
        for name, unit, qty in items:
            c.add_item(name, unit, qty)
        subtotal = calc_subtotal(items)
        expected = round(subtotal + shipping_fee(subtotal), 2)
        assert c.total() == expected

    def test_total_with_valid_coupon(self):
        c = Cart()
        c.add_item("widget", 10.00, 3)  # subtotal 30
        coupon_code = "SAVE20"
        percent = parse_coupon(coupon_code)
        discounted_subtotal = round(30 * (1 - percent / 100), 2)
        expected_total = round(discounted_subtotal + shipping_fee(discounted_subtotal), 2)
        assert c.total(coupon=coupon_code) == expected_total

    def test_invalid_coupon_raises(self):
        c = Cart()
        c.add_item("item", 5.00, 1)
        with pytest.raises(ValueError):
            c.total(coupon="INVALID")

    def test_member_discount_shipping_reduction(self):
        c = Cart()
        c.add_item("book", 15.00, 2)  # subtotal 30
        assert shipping_fee(30, member=True) < shipping_fee(30)
        expected_total = round(30 + shipping_fee(30, member=True), 2)
        assert c.total(member=True) == expected_total
