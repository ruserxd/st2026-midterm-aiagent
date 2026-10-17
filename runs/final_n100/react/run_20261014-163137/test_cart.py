import pytest

import cart

# Helper to create a cart with specified items

def make_cart(items):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, quantity=qty)
    return c

class TestCartTotal:
    def test_empty_cart(self):
        c = cart.Cart()
        assert c.total() == 0

    def test_no_coupon_no_shipping_fee(self):
        # subtotal below free shipping threshold
        c = make_cart([
            ('item1', 200, 2),   # 400
            ('item2', 150, 1),   # 150
        ])
        # subtotal 550 < 1000 -> fee 60
        assert c.total() == pytest.approx(550 + 60, rel=1e-9)

    def test_no_coupon_member_shipping_fee(self):
        c = make_cart([
            ('item', 400, 1),   # subtotal 400
        ])
        expected_total = 400 + 30  # member pays half of 60
        assert c.total(member=True) == pytest.approx(expected_total)

    def test_free_shipping_threshold(self):
        c = make_cart([
            ('big', 500, 3),   # subtotal 1500 >= 1000 -> free shipping
        ])
        assert c.total() == 1500

    def test_coupon_application(self):
        c = make_cart([
            ('item', 400, 1),   # subtotal 400
        ])
        # Coupon 10% discount
        total_after_discount = 400 * 0.9 + 60  # shipping fee applied after coupon
        assert c.total(coupon='10%') == pytest.approx(total_after_discount)

    def test_invalid_coupon_raises(self):
        c = make_cart([
            ('item', 100, 1),
        ])
        with pytest.raises(ValueError):
            c.total(coupon='invalid')

    def test_rounding_to_two_decimals(self):
        c = cart.Cart()
        # add item that results in a non-integer total before rounding
        c.add_item('precise', 333.333, quantity=3)  # subtotal 999.999
        # Apply no coupon, member shipping half of 60 -> 30
        expected = round(999.999 + 30, 2)
        assert c.total(member=True) == pytest.approx(expected)

    def test_coupon_percent_parsing(self):
        # ensure parse_coupon correctly interprets percent strings
        assert cart.parse_coupon('5%') == 5
        assert cart.parse_coupon('12.5%') == 12.5
        with pytest.raises(ValueError):
            cart.parse_coupon('20')  # missing % sign
    
    def test_bulk_discount_percent_function(self):
        # Not directly related to total, but ensure helper works as spec
        assert cart.bulk_discount_percent(2) == 0
        assert cart.bulk_discount_percent(5) == 10
        assert cart.bulk_discount_percent(15) == 20
