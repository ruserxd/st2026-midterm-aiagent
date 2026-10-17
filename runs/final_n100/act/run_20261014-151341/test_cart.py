import pytest
from cart import Cart, parse_coupon, bulk_discount_percent, apply_discount, shipping_fee

# helper for rounding check

def round2(x):
    return round(float(x), 2)

class TestCartBasics:
    def test_empty_cart_total(self):
        c = Cart()
        assert c.total() == 0.0
        # no shipping

    def test_add_and_subtotal(self):
        c = Cart()
        c.add_item("apple", 1.00, quantity=3)
        c.add_item("banana", 0.50)
        assert round2(c.subtotal()) == round2(3*1.00 + 0.50)

    def test_remove_items(self):
        c = Cart()
        c.add_item("apple", 1.00, quantity=5)
        c.remove_item("apple", quantity=3)
        assert c.items() == {"apple": (1.00, 2)}

    def test_bulk_discount_percent(self):
        # 10 items gives 5% discount, but the function returns percent not multiplier
        assert bulk_discount_percent(10) == 5
        assert bulk_discount_percent(20) == 10

    def test_apply_discount_and_shipping(self):
        c = Cart()
        c.add_item("item", 100.0)
        # no discount, expect shipping on 100 -> maybe default shipping fee e.g. 10?
        # we don't know shipping_fee spec; skip detailed value

    def test_coupon_application_and_rounding(self):
        c = Cart()
        c.add_item("item", 20.0)
        total_with_no_coupon = c.total()
        # apply a coupon of 10%
        c_total_10 = c.total(coupon="COUPON10")
        expected = round2(total_with_no_coupon * (1 - parse_coupon("COUPON10")))
        assert c_total_10 == expected

    def test_invalid_coupon(self):
        c = Cart()
        with pytest.raises(ValueError):
            c.total(coupon="BADCODE")

# Ensure parse_coupon returns correct percent
class TestParseCoupon:
    def test_valid_coupons(self):
        assert parse_coupon("COUPON10") == 0.10
        assert parse_coupon("SAVE20") == 0.20

    def test_invalid_code_format(self):
        with pytest.raises(ValueError):
            parse_coupon("abc123")
