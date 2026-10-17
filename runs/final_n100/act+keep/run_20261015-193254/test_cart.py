import cart
import pytest

def approx(value):
    return round(float(value), 2)

class TestApplyDiscount:
    def test_basic(self):
        assert cart.apply_discount(200, 15) == 170.0
    def test_no_discount(self):
        assert cart.apply_discount(100, 0) == 100.0
    def test_full_discount(self):
        assert cart.apply_discount(120, 100) == 0.0
    def test_rounding(self):
        # 99 with 33% discount -> 66.03
        assert cart.apply_discount(99, 33) == approx(99 * 0.67)
    def test_negative_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10, 20)
    def test_invalid_percent(self):
        for p in (-5, 101):
            with pytest.raises(ValueError):
                cart.apply_discount(100, p)

class TestBulkDiscountPercent:
    def test_excessive_quantity(self):
        assert cart.bulk_discount_percent(200) == 15
    def test_medium_quantity(self):
        assert cart.bulk_discount_percent(75) == 10
    def test_low_quantity(self):
        assert cart.bulk_discount_percent(12) == 5
    def test_no_discount(self):
        assert cart.bulk_discount_percent(9) == 0
    def test_zero_or_negative(self):
        for q in (0, -3):
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(q)

class TestParseCoupon:
    def test_valid_codes_case_insensitive(self):
        assert cart.parse_coupon("SAVE10") == 10
        # The implementation currently does not handle case-insensitivity.
        # According to the specification, this should pass.
        assert cart.parse_coupon("save20") == 20
        assert cart.parse_coupon("   SaVe30  ") == 30
    def test_invalid_range_and_format(self):
        for code in ("SAVE0", "SAVE51", "INVALID", "SAVEX", "SAVEx10"):
            with pytest.raises(ValueError):
                cart.parse_coupon(code)

class TestShippingFee:
    def test_free_for_large_subtotal(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500.50) == 0
    def test_standard_non_member(self):
        assert cart.shipping_fee(500) == 60
    def test_member_half_fee(self):
        assert cart.shipping_fee(200, member=True) == 30
    def test_negative_subtotal(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

class TestCartSubtotal:
    def setup_cart(self, items):
        c = cart.Cart()
        for name, price, qty in items:
            c.add_item(name, price, quantity=qty)
        return c
    def test_empty_cart(self):
        assert self.setup_cart([]).subtotal() == 0.0
    def test_single_item_no_discount(self):
        c = self.setup_cart([("apple", 10, 3)])
        # no bulk discount
        assert c.subtotal() == 30.0
    def test_bulk_discounts(self):
        c = self.setup_cart([
            ("widget", 100, 12),   # 5% off
            ("gadget", 200, 55),   # 10% off
            ("doodad", 50, 120),   # 15% off
        ])
        total = (
            cart.apply_discount(100*12, 5) +
            cart.apply_discount(200*55, 10) +
            cart.apply_discount(50*120, 15)
        )
        assert c.subtotal() == round(total, 2)

class TestCartTotal:
    def test_empty_cart(self):
        assert cart.Cart().total() == 0.0
    def test_subtotal_only(self):
        c = cart.Cart()
        c.add_item("item", 100, quantity=1)
        # subtotal 100, shipping 60 -> total 160
        assert c.total() == 160.0
    def test_member_shipping_half_fee(self):
        c = cart.Cart()
        c.add_item("item", 200, quantity=1)
        # subtotal 200, member half fee 30 -> total 230
        assert c.total(member=True) == 230.0
    def test_coupon_reduction_before_shipping(self):
        c = cart.Cart()
        c.add_item("product", 500, quantity=2)  # subtotal 1000 => free shipping
        assert c.total(coupon="SAVE10") == round(1000 * 0.9, 2)
    def test_coupon_and_shipping(self):
        c = cart.Cart()
        c.add_item("product", 200, quantity=1)  # subtotal 200
        # coupon SAVE20 reduces to 160, shipping 60 -> total 220
        assert c.total(coupon="SAVE20") == 220.0
    def test_invalid_coupon(self):
        c = cart.Cart()
        c.add_item("item", 100)
        with pytest.raises(ValueError):
            c.total(coupon="BADCODE")
