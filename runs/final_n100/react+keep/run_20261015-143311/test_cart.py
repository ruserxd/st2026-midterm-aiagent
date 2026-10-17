import pytest
import cart

# Helper rounding function consistent with implementation
round2 = lambda x: round(float(x), 2)

class TestApplyDiscount:
    def test_valid_discount(self):
        assert cart.apply_discount(200, 15) == 170.0
        assert cart.apply_discount(100, 0) == 100.0
        assert cart.apply_discount(100, 100) == 0.0

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-1, 10)

    def test_invalid_percent(self):
        for bad in (-5, 105):
            with pytest.raises(ValueError):
                cart.apply_discount(100, bad)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize("qty,expected", [
        (9, 0),   # less than 10
        (10, 5),  # boundary 10
        (49, 5),
        (50, 10), # boundary 50
        (99, 10),
        (100, 15),# boundary 100
        (150, 15)
    ])
    def test_bounds(self, qty, expected):
        assert cart.bulk_discount_percent(qty) == expected

    def test_invalid_quantity(self):
        for bad in (0, -5, 3.5):
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(bad)

class TestParseCoupon:
    @pytest.mark.parametrize("code", ["SAVE10", "save20", " SaVe30 "])
    def test_valid_codes(self, code):
        assert cart.parse_coupon(code) in {10, 20, 30}

    def test_invalid_format(self):
        for bad in ["SAV5", "SAVE-5", "SAVE101", "123", ""]:
            with pytest.raises(ValueError):
                cart.parse_coupon(bad)

class TestShippingFee:
    @pytest.mark.parametrize("subtotal,expected", [
        (0, 60),
        (500, 60),
        (999.99, 60),
        (1000, 0),
        (1500, 0)
    ])
    def test_non_member(self, subtotal, expected):
        assert cart.shipping_fee(subtotal) == expected

    @pytest.mark.parametrize("subtotal,expected", [
        (500, 30),   # half fee for members
        (999.99, 30)
    ])
    def test_member(self, subtotal, expected):
        assert cart.shipping_fee(subtotal, member=True) == expected

    def test_invalid_subtotal(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

# ---------- Tests for Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert isinstance(self.cart.items(), dict)
        assert len(self.cart.items()) == 0
        assert self.cart.subtotal() == 0

    def test_add_and_subtract_items(self):
        # Add new item with bulk discount boundary
        self.cart.add_item("apple", 2.0, quantity=10)  # qualifies for 5% discount
        assert self.cart.items()["apple"] == 10
        expected_line_total = cart.apply_discount(2.0 * 10, cart.bulk_discount_percent(10))
        assert self.cart.subtotal() == round2(expected_line_total)

    def test_add_item_invalid_price_or_qty(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1, quantity=2)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.5, quantity=0)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 3.0, quantity=2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4.0, quantity=1)

    def test_remove_item_and_zero_removal_bug(self):
        self.cart.add_item("pear", 5.0, quantity=3)
        # Remove part of it
        self.cart.remove_item("pear", quantity=2)
        assert self.cart.items()["pear"] == 1
        # Removing the remaining quantity should delete the item per spec (<=0)
        self.cart.remove_item("pear", quantity=1)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent_item(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_total_with_coupon_and_shipping_bug(self):
        # Two items with different bulk discounts
        self.cart.add_item("widget", 100.0, quantity=10)  # 5% bulk discount
        self.cart.add_item("gizmo", 50.0, quantity=200)   # 15% bulk discount
        subtotal = self.cart.subtotal()
        amount_after_coupon = round2(subtotal * (1 - cart.parse_coupon("SAVE20") / 100))
        shipping_fee_expected = cart.shipping_fee(amount_after_coupon, member=False)
        expected_total = round2(amount_after_coupon + shipping_fee_expected)
        assert self.cart.total(coupon="SAVE20") == expected_total

    def test_total_member_and_coupon(self):
        # Subtotal 1000 -> free shipping per spec when subtotal>=1000 after coupon
        self.cart.add_item("item", 200.0, quantity=5)  # subtotal before discount: 1000
        amount_after_discount = round2(200.0 * 5 * (1 - cart.parse_coupon("SAVE10") / 100))
        shipping_fee_expected = cart.shipping_fee(amount_after_discount, member=True)
        total_with_coupon_member = round2(amount_after_discount + shipping_fee_expected)
        assert self.cart.total(member=True, coupon="SAVE10") == total_with_coupon_member

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
