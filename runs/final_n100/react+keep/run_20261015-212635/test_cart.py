import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Utility function for comparison with rounding ---------

def round2(value):
    return round(value, 2)

# ------------ Tests for simple utility functions ------------------

class TestApplyDiscount:
    def test_normal_discount(self):
        assert apply_discount(200, 15) == 170.0

    def test_zero_percent(self):
        assert apply_discount(100, 0) == 100.0

    def test_full_percent(self):
        assert apply_discount(123.45, 100) == 0.0

    @pytest.mark.parametrize(
        "price", [-1, -10],
    )
    def test_negative_price_raises(self, price):
        with pytest.raises(ValueError):
            apply_discount(price, 10)

    @pytest.mark.parametrize(
        "percent", [-5, 101, 150],
    )
    def test_invalid_percent_raises(self, percent):
        with pytest.raises(ValueError):
            apply_discount(50, percent)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize(
        "quantity, expected",
        [
            (5, 0),
            (10, 5),
            (15, 5),
            (49, 5),
            (50, 10),
            (75, 10),
            (99, 10),
            (100, 15),
            (150, 15),
        ],
    )
    def test_expected_discounts(self, quantity, expected):
        assert bulk_discount_percent(quantity) == expected

    @pytest.mark.parametrize(
        "quantity", [0, -1, -10],
    )
    def test_invalid_quantity_raises(self, quantity):
        with pytest.raises(ValueError):
            bulk_discount_percent(quantity)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code, expected",
        [("SAVE5", 5), ("save10", 10), (" Save20 ", 20)],
    )
    def test_valid_codes(self, code, expected):
        assert parse_coupon(code) == expected

    @pytest.mark.parametrize(
        "code",
        ["SAVE0", "SAVE51", "DISCOUNT10", "sve10", "save"],
    )
    def test_invalid_codes_raises(self, code):
        with pytest.raises(ValueError):
            parse_coupon(code)

class TestShippingFee:
    @pytest.mark.parametrize(
        "subtotal, member, expected",
        [
            (0, False, 60),
            (500, True, 30),
            (999.99, False, 60),
            (1000, False, 0),
            (1500, True, 0),
        ],
    )
    def test_expected_fees(self, subtotal, member, expected):
        assert shipping_fee(subtotal, member) == expected

    @pytest.mark.parametrize(
        "subtotal",
        [-1, -10],
    )
    def test_negative_subtotal_raises(self, subtotal):
        with pytest.raises(ValueError):
            shipping_fee(subtotal, False)

# ------------------------ Cart tests ------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 10.0, quantity=3)
        self.cart.add_item("banana", 5.0)
        assert self.cart.items() == {"apple": 3, "banana": 1}

    def test_bulk_discount_in_subtotal(self):
        # 12 apples -> bulk discount 5% on line
        self.cart.add_item("apple", 10.0, quantity=12)
        expected_line = apply_discount(120.0, 5)  # 10*12=120
        assert self.cart.subtotal() == round2(expected_line)

    def test_total_without_coupon(self):
        self.cart.add_item("apple", 10.0, quantity=12)
        # subtotal already includes bulk discount
        amount = self.cart.total(member=False)
        # shipping: subtotal 120 -> no discount on shipping (non-member) => 60
        assert amount == round2(self.cart.subtotal() + shipping_fee(self.cart.subtotal(), False))

    def test_total_with_valid_coupon_and_member(self):
        self.cart.add_item("item", 100.0, quantity=10)  # 5% bulk discount -> line = apply_discount(1000,5)
        subtotal_after_bulk = round2(apply_discount(1000, 5))
        # coupon SAVE10 gives 10% off on amount after bulk
        after_coupon = round2(subtotal_after_bulk * 0.90)
        shipping = shipping_fee(after_coupon, True)  # member => half if not free
        total_expected = round2(after_coupon + shipping)
        assert self.cart.total(member=True, coupon="SAVE10") == total_expected

    def test_total_with_invalid_coupon_raises(self):
        self.cart.add_item("item", 20.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_empty_cart_no_shipping(self):
        assert self.cart.total() == 0

    def test_remove_item_and_quantity_limits(self):
        self.cart.add_item("book", 15.0, quantity=5)
        self.cart.remove_item("book", quantity=2)
        assert self.cart.items()["book"] == 3
        # remove more than existing to trigger deletion
        self.cart.remove_item("book", quantity=3)
        assert "book" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist")
