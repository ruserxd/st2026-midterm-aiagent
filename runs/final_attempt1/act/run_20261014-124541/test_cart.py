import pytest
from cart import Cart, parse_coupon, apply_discount, shipping_fee, bulk_discount_percent

# Helper to create a cart with items

def make_cart(items):
    c = Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

class TestCartTotal:
    def test_empty_cart_total(self):
        c = Cart()
        assert c.total() == 0

    def test_subtotal_and_shipping_no_coupon_member_false(self):
        # Two items: Apple $2 each *3, Banana $1.5 each *2 = subtotal 9.0
        c = make_cart([
            ('Apple', 2.0, 3),
            ('Banana', 1.5, 2)
        ])
        # No coupon, member=False
        subtotal = 9.0
        shipping = shipping_fee(subtotal, member=False)
        expected_total = round(subtotal + shipping, 2)
        assert c.total() == expected_total

    def test_shipping_for_member(self):
        c = make_cart([('Orange', 5.0, 1)])
        subtotal = 5.0
        shipping_no = shipping_fee(subtotal, member=False)
        shipping_yes = shipping_fee(subtotal, member=True)
        assert shipping_yes < shipping_no
        expected_total = round(subtotal + shipping_yes, 2)
        assert c.total(member=True) == expected_total

    def test_coupon_application(self):
        # Coupon 'SAVE10' reduces by 10% per spec of parse_coupon
        c = make_cart([('Gadget', 100.0, 1)])
        subtotal = 100.0
        percent = parse_coupon('SAVE10')
        discounted = apply_discount(subtotal, percent)
        shipping = shipping_fee(discounted, member=False)
        expected_total = round(discounted + shipping, 2)
        assert c.total(coupon='SAVE10') == expected_total

    def test_invalid_coupon_raises(self):
        c = make_cart([('Thing', 50.0, 1)])
        with pytest.raises(ValueError):
            c.total(coupon='INVALIDCODE')

    @pytest.mark.parametrize("quantity,expected_percent",[
        (1,0),
        (9,0),
        (10,5),
        (49,5),
        (50,10),
        (99,10),
        (100,15)
    ])
    def test_bulk_discount_percent(self, quantity, expected_percent):
        assert bulk_discount_percent(quantity) == expected_percent

    @pytest.mark.parametrize("quantity",[-5,0])
    def test_bulk_discount_invalid_quantity_raises(self, quantity):
        with pytest.raises(ValueError):
            bulk_discount_percent(quantity)
