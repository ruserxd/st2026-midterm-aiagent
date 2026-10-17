import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Utility helpers ----------

def almost_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---------- Function tests ----------

class TestApplyDiscount:
    def test_basic_discount(self):
        assert apply_discount(200, 15) == 170.0

    @pytest.mark.parametrize(
        "price,percent",
        [(-10, 10), (100, -5), (100, 105)],
    )
    def test_invalid_arguments(self, price, percent):
        with pytest.raises(ValueError):
            apply_discount(price, percent)

class TestBulkDiscountPercent:
    def test_thresholds(self):
        assert bulk_discount_percent(5) == 0
        assert bulk_discount_percent(10) == 5
        assert bulk_discount_percent(50) == 10
        assert bulk_discount_percent(100) == 15

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            bulk_discount_percent(quantity)

class TestParseCoupon:
    def test_valid_codes(self):
        assert parse_coupon("SAVE10") == 10
        assert parse_coupon("  save25  ") == 25

    @pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "   SAVE-5  "])
    def test_invalid_codes(self, code):
        with pytest.raises(ValueError):
            parse_coupon(code)

class TestShippingFee:
    def test_free_shipping_threshold(self):
        assert shipping_fee(1000) == 0
        assert shipping_fee(2000.50) == 0

    @pytest.mark.parametrize("subtotal", [500, 999.99])
    def test_nonfree_fee(self, subtotal):
        assert shipping_fee(subtotal) == 60
        assert shipping_fee(subtotal, member=True) == 30

    @pytest.mark.parametrize("subtotal", [-10, -0.01])
    def test_negative_subtotal_raises(self, subtotal):
        with pytest.raises(ValueError):
            shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 3}
        # adding same item increases quantity if price matches
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 50, 0)

    def test_add_price_mismatch(self):
        self.cart.add_item("milk", 200, 1)
        with pytest.raises(ValueError):
            # different unit price should raise ValueError
            self.cart.add_item("milk", 250, 2)

    def test_remove_and_items(self):
        self.cart.add_item("bread", 150, 4)
        self.cart.remove_item("bread", 2)
        assert self.cart.items() == {"bread": 2}
        # removing more than remaining removes item entirely
        self.cart.remove_item("bread", 3)
        assert "bread" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("chocolate", 1)

    def test_subtotal_no_discounts(self):
        self.cart.add_item("pen", 50, 2)
        assert self.cart.subtotal() == 100.0

    def test_subtotal_bulk_discount(self):
        # 10 items -> bulk discount 5%
        self.cart.add_item("notebook", 200, 10)
        expected = apply_discount(200 * 10, 5)  # 2000 * 0.95
        assert almost_equal(self.cart.subtotal(), expected)

    def test_total_no_coupon_or_shipping(self):
        self.cart.add_item("sticker", 30, 3)
        assert self.cart.total() == 90.0

    def test_total_with_coupon_and_nonfree_shipping(self):
        # subtotal = 200, coupon SAVE10 -> reduce by 10% => 180
        # shipping fee on 180 (non-member) = 60
        self.cart.add_item("toy", 200, 1)
        total = self.cart.total(coupon="SAVE10")
        expected_total = apply_discount(200, 10) + 60
        assert almost_equal(total, expected_total)

    def test_total_with_member_and_coupon(self):
        # subtotal = 2000, member -> shipping free, coupon SAVE20 => 1600
        self.cart.add_item("camera", 2000, 1)
        total = self.cart.total(member=True, coupon="SAVE20")
        expected_total = apply_discount(2000, 20)  # no shipping fee
        assert almost_equal(total, expected_total)

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", 100, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0

# ---------- Edge Cases and Roundings ----------
class TestRounding:
    def test_apply_discount_rounding(self):
        # 33% of 10 = 3.3, result 6.7, should round to two decimals
        assert apply_discount(10, 33) == 6.70

    def test_shipping_fee_and_total_rounding(self):
        # subtotal 333 with 5% bulk discount => 316.35, coupon 15% => 269.4975 -> rounded 269.50 + shipping
        self.cart = Cart()
        self.cart.add_item("widget", 333, 10)
        total = self.cart.total(coupon="SAVE15")
        # compute expected stepwise
        discounted_subtotal = apply_discount(333 * 10, 5)  # bulk discount
        coupon_amount = apply_discount(discounted_subtotal, 15)
        fee = shipping_fee(coupon_amount)
        expected = round(coupon_amount + fee, 2)
        assert almost_equal(total, expected)
