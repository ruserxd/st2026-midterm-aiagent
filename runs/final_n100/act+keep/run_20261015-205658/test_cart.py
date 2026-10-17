import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --------------------
# tests for helper functions
# --------------------

class TestApplyDiscount:
    def test_basic(self):
        assert apply_discount(200, 15) == 170.0

    def test_rounding(self):
        # 99 * 12.5% = 87.375 -> round to 2 decimals
        assert apply_discount(99, 12.5) == 86.625

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            apply_discount(-1, 10)

    def test_invalid_percent_low(self):
        with pytest.raises(ValueError):
            apply_discount(100, -5)

    def test_invalid_percent_high(self):
        with pytest.raises(ValueError):
            apply_discount(100, 105)

class TestBulkDiscountPercent:
    def test_below_10(self):
        assert bulk_discount_percent(9) == 0

    def test_at_10(self):
        assert bulk_discount_percent(10) == 5

    def test_at_50(self):
        assert bulk_discount_percent(50) == 10

    def test_above_100(self):
        assert bulk_discount_percent(150) == 15

    def test_invalid_quantity_type(self):
        with pytest.raises(ValueError):
            bulk_discount_percent(-3)
        with pytest.raises(ValueError):
            bulk_discount_percent(0)

class TestParseCoupon:
    def test_valid_code_case_insensitive_and_whitespace(self):
        assert parse_coupon("SAVE10") == 10
        assert parse_coupon("save20") == 20
        assert parse_coupon(" SAVE30 ") == 30

    def test_invalid_n_out_of_range(self):
        with pytest.raises(ValueError):
            parse_coupon("SAVE0")
        with pytest.raises(ValueError):
            parse_coupon("SAVE51")

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_coupon("NOTACODE")
        with pytest.raises(ValueError):
            parse_coupon("SAVEX10")

class TestShippingFee:
    def test_free_for_high_subtotal(self):
        assert shipping_fee(1000) == 0
        assert shipping_fee(1500) == 0

    def test_regular_fee_non_member(self):
        assert shipping_fee(500) == 60

    def test_member_half_fee(self):
        assert shipping_fee(300, member=True) == 30

    def test_invalid_subtotal_negative(self):
        with pytest.raises(ValueError):
            shipping_fee(-1)

# --------------------
# tests for Cart class
# --------------------

class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initially_empty(self):
        assert list(self.cart.items()) == []
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 60  # no items, shipping fee 60 for subtotal 0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("Apple", 100, quantity=2)
        assert list(self.cart.items()) == [({"name": "Apple", "unit_price": 100.0, "quantity": 2}, 200.0)]
        # add same item increases quantity
        self.cart.add_item("Apple", 100)
        assert any(it[0]["quantity"] == 3 for it in self.cart.items())

    def test_add_invalid_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("Banana", -10)
        with pytest.raises(ValueError):
            self.cart.add_item("Banana", 20, quantity=0)

    def test_add_different_unit_price_error(self):
        self.cart.add_item("Orange", 50)
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", 60)

    def test_remove_item_and_removal_edge(self):
        self.cart.add_item("Peach", 80, quantity=3)
        # remove less than existing
        self.cart.remove_item("Peach", quantity=2)
        assert any(it[0]["quantity"] == 1 for it in self.cart.items())
        # removing remaining removes item entirely
        self.cart.remove_item("Peach")
        assert list(self.cart.items()) == []

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Mango")

    def test_subtotal_with_bulk_discount(self):
        # 10 units => bulk discount 5%
        self.cart.add_item("Tomato", 200, quantity=10)
        assert self.cart.subtotal() == apply_discount(2000, 5)

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("Bread", 150, quantity=4)  # subtotal 600
        expected = apply_discount(600, 0)  # no bulk discount because only one item
        expected += shipping_fee(expected)
        assert self.cart.total() == expected

    def test_total_with_member_shipping(self):
        self.cart.add_item("Milk", 120, quantity=2)  # subtotal 240
        expected = apply_discount(240, 0)
        expected += shipping_fee(expected, member=True)
        assert self.cart.total(member=True) == expected

    def test_total_with_coupon(self):
        self.cart.add_item("Cheese", 300, quantity=5)
        # coupon gives e.g., 10%
        total = self.cart.total(coupon="SAVE10")
        # compute expected manually: subtotal 1500 -> bulk discount 5% (since 5<10) -> 1425
        # shipping fee 60 => 1485; then apply 10% coupon -> 1336.5
        assert total == pytest.approx(1336.5)

    def test_total_with_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
