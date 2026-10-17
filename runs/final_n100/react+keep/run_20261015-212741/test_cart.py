import pytest
from cart import Cart, parse_coupon, apply_discount

# Helper: create cart with single item

def make_cart(price, quantity=1):
    c = Cart()
    c.add_item("item", price, quantity)
    return c

class TestCartSubtotal:
    def test_simple(self):
        c = make_cart(100, 2)  # subtotal 200
        assert c.subtotal() == 200

    def test_multiple_items(self):
        c = Cart()
        c.add_item("apple", 50, 1)
        c.add_item("banana", 30, 3)
        assert c.subtotal() == 50 + 30*3

class TestCartTotal:
    def test_no_coupon_non_member(self):
        c = make_cart(900)  # subtotal 900 < 1000 => shipping 60
        assert c.total() == 960  # 900+60 rounded to 2 decimals

    def test_no_coupon_member(self):
        c = make_cart(800)
        assert c.total(member=True) == 830  # 800 + 30

    def test_with_valid_coupon(self):
        c = make_cart(1000, 1)
        # apply 20% discount => 800; shipping free because subtotal >= 1000 after discount
        assert c.total(coupon="SAVE20") == 800.00

    def test_coupon_applied_before_shipping(self):
        c = make_cart(900)  # subtotal 900, no discount, shipping 60 -> 960
        # apply coupon to reduce below free threshold
        assert c.total(coupon="SAVE10") == round(900*0.9 + 60, 2)

    def test_invalid_coupon_raises(self):
        c = make_cart(500)
        with pytest.raises(ValueError):
            c.total(coupon="INVALIDCODE")

    def test_empty_cart_returns_zero(self):
        c = Cart()
        assert c.total() == 0

class TestParseCoupon:
    def test_valid_code_case_insensitive(self):
        assert parse_coupon("SAVE10") == 10
        assert parse_coupon("save10") == 10
        assert parse_coupon("   SaVe30  ") == 30

    def test_invalid_codes_raise(self):
        for code in ["", "SAVEX", "10SAVE", "SAVE51"]:
            with pytest.raises(ValueError):
                parse_coupon(code)

# Edge case: discount makes subtotal exceed free shipping threshold
class TestTotalAfterDiscountFreeShipping:
    def test_discount_pushes_above_free_threshold(self):
        # subtotal 900, apply coupon of 20% => 720 <1000 so still not free. Need higher original.
        c = make_cart(1200)
        assert c.total(coupon="SAVE10") == round(1200*0.9 + 60, 2)  # 1080+60=1140
        # But if subtotal after discount >=1000 shipping free
        c = make_cart(1100)
        assert c.total(coupon="SAVE10") == round(1100*0.9, 2)  # 990 no shipping

# Test rounding behaviour
class TestRounding:
    def test_rounding_to_two_decimals(self):
        c = make_cart(999.99)
        assert c.total(coupon="SAVE5") == round(999.99*0.95 + 60, 2)
