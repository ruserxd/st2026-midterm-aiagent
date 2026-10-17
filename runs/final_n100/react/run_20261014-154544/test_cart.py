import pytest
from cart import Cart, parse_coupon, shipping_fee

# Helper to get subtotal with items

def make_cart(items):
    c = Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

class TestCartTotal:
    def test_empty_cart(self):
        c = Cart()
        assert c.total() == 0

    def test_without_coupon(self):
        # subtotal: $10 * 2 = 20
        c = make_cart([("apple", 10, 2)])
        # shipping_fee for 20 with default member False is 5.0 (see spec)
        expected_total = round(20 + shipping_fee(20), 2)
        assert c.total() == expected_total

    def test_with_valid_coupon(self):
        # subtotal: $50
        c = make_cart([("widget", 25, 2)])
        # coupon '10P' -> 10% off
        discount_amount = parse_coupon('10P')
        discounted_subtotal = round(50 * (1 - discount_amount/100), 2)
        expected_total = round(discounted_subtotal + shipping_fee(discounted_subtotal), 2)
        assert c.total(coupon='10P') == expected_total

    def test_with_invalid_coupon(self):
        c = make_cart([("widget", 25, 1)])
        with pytest.raises(ValueError):
            c.total(coupon="BAD")

    def test_member_shipping_fee(self):
        # subtotal: $30
        c = make_cart([("gadget", 15, 2)])
        discounted_subtotal = 30  # no coupon
        # member flag should reduce shipping fee per spec of shipping_fee
        total_no_member = round(discounted_subtotal + shipping_fee(discounted_subtotal), 2)
        total_member = round(discounted_subtotal + shipping_fee(discounted_subtotal, member=True), 2)
        assert c.total() == total_no_member
        assert c.total(member=True) == total_member
