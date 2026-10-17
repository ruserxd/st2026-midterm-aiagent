import pytest
import cart

# ---------- Helper functions for expected values based on specification ----------

def expected_apply_discount(price, percent):
    if price < 0:
        raise ValueError("price must be non-negative")
    if not (0 <= percent <= 100):
        raise ValueError("percent must be between 0 and 100 inclusive")
    return round(price * (1 - percent / 100.0), 2)

# ---------- Tests for utility functions ----------

class TestApplyDiscount:
    def test_basic_discount(self):
        assert cart.apply_discount(200, 15) == 170.0

    def test_zero_and_full_percent(self):
        assert cart.apply_discount(100, 0) == 100.0
        assert cart.apply_discount(50, 100) == 0.0

    def test_rounding(self):
        # 10% of 33 gives 29.7 -> round to two decimals
        assert cart.apply_discount(33, 10) == 29.7

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-5, 20)

    def test_invalid_percent(self):
        for bad in (-1, 101):
            with pytest.raises(ValueError):
                cart.apply_discount(100, bad)

class TestBulkDiscountPercent:
    def test_quantities(self):
        assert cart.bulk_discount_percent(5) == 0
        assert cart.bulk_discount_percent(10) == 5
        assert cart.bulk_discount_percent(15) == 5
        assert cart.bulk_discount_percent(50) == 10
        assert cart.bulk_discount_percent(51) == 10
        assert cart.bulk_discount_percent(100) == 15

    def test_invalid_quantity(self):
        for bad in (0, -3):
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(bad)

class TestParseCoupon:
    def test_valid_codes(self):
        assert cart.parse_coupon("SAVE10") == 10
        assert cart.parse_coupon(" save20 ") == 20
        assert cart.parse_coupon("SaVe5") == 5

    def test_invalid_codes(self):
        for bad in ["", "SAVEXX", "DISCOUNT", "save0", "save51", "save-10"]:
            with pytest.raises(ValueError):
                cart.parse_coupon(bad)

class TestShippingFee:
    def test_free_shipping(self):
        assert cart.shipping_fee(1000, member=False) == 0
        assert cart.shipping_fee(2000, member=True) == 0

    def test_nonfree_for_members_and_nonmembers(self):
        assert cart.shipping_fee(500, member=False) == 60
        assert cart.shipping_fee(999.99, member=True) == 30

    def test_invalid_subtotal(self):
        for bad in (-10, -1e-3):
            with pytest.raises(ValueError):
                cart.shipping_fee(bad)

# ---------- Tests for Cart class ----------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple": 3}
        # Add same item increases quantity
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 5}
        # Adding with different price raises error
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 2.0, 1)

    def test_remove_item(self):
        self.cart.add_item("banana", 2.0, 4)
        self.cart.remove_item("banana", 2)
        assert self.cart.items() == {"banana": 2}
        # Removing more than exists should remove the item
        self.cart.remove_item("banana", 3)  # reduces to -1 -> removal
        assert "banana" not in self.cart.items()
        with pytest.raises(KeyError):
            self.cart.remove_item("cherry")

    def test_subtotal_bulk_discount(self):
        # 10 units of 10 each => bulk discount 5% on 100 = 95.0
        self.cart.add_item("item1", 10, 10)
        assert self.cart.subtotal() == 95.0
        # 50 units -> 10% discount on 500 = 450.0
        self.cart.remove_item("item1")
        self.cart.add_item("item2", 20, 50)
        assert self.cart.subtotal() == 450.0
        # Mixed items with different discounts
        self.cart.add_item("item3", 5, 5)  # no discount
        expected = 450.0 + 25.0  # item2 + item3
        assert self.cart.subtotal() == round(expected, 2)

    def test_total_no_coupon_no_member(self):
        self.cart.add_item("product", 100, 10)  # subtotal 950 after 5% discount
        # No coupon, non-member: shipping fee 60 on amount before coupon (950 < 1000)
        expected = round(950 + 60, 2)
        assert self.cart.total(member=False) == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("prod", 200, 10)  # subtotal 1900 after 5% discount
        amount_before_shipping = 1900  # >=1000 -> free shipping if no coupon? actually shipping based on amount after coupon
        # Apply a 20% coupon => 1520
        # Shipping fee for non-member on 1900 is 0, but should be computed on 1520 -> still 0
        total = self.cart.total(member=False, coupon="SAVE20")
        assert total == round(1520 + 0, 2)

    def test_total_shipping_after_coupon_member(self):
        # subtotal 500 after bulk discount
        self.cart.add_item("prod", 50, 10)  # unit*qty = 500; 5% => 475
        amount_with_coupon = cart.apply_discount(475, 10)  # apply 10% coupon => 427.5
        # Shipping fee for member on subtotal 475 is 30 (half of 60)
        expected_total = round(amount_with_coupon + 30, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_invalid_coupon_in_total_raises(self):
        self.cart.add_item("item", 10, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
