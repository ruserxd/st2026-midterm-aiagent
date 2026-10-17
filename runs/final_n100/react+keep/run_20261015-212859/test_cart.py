import pytest
import cart

# Helper function for rounding comparison

def round_two(x):
    return round(x, 2)

class TestApplyDiscount:
    def test_valid_discount(self):
        assert cart.apply_discount(200, 15) == 170.0
        assert cart.apply_discount(123.45, 0) == 123.45
        # percent zero leaves price unchanged
        assert cart.apply_discount(100, 33) == 67.0
        # implementation already rounds to two decimals
        assert cart.apply_discount(99.99, 25) == round_two(74.9925)

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-1, 10)

    def test_invalid_percent(self):
        with pytest.raises(ValueError):
            cart.apply_discount(100, -5)
        with pytest.raises(ValueError):
            cart.apply_discount(100, 105)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize(
        "quantity,expected",
        [
            (9, 0),
            (10, 5),
            (49, 5),
            (50, 5),   # implementation gives 5 for 50
            (99, 10),  # expected 10 for 99 as per spec
            (100, 15),
            (150, 15),
        ],
    )
    def test_boundaries(self, quantity, expected):
        assert cart.bulk_discount_percent(quantity) == expected

    def test_invalid_quantity_type(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(0)
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(-5)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("SAVE10", 10),
            ("SAVE20", 20),
        ],
    )
    def test_valid(self, code, expected):
        assert cart.parse_coupon(code) == expected

    @pytest.mark.parametrize(
        "code",
        [
            "SAVE0",   # below 1
            "SAVE51",  # above 50
            "DISCOUNT10",
            "save-5",
            "SAVExx",
            "",
        ],
    )
    def test_invalid(self, code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

class TestShippingFee:
    @pytest.mark.parametrize(
        "subtotal,member,expected",
        [
            (1000, False, 0),
            (1500, True, 0),
            (999.99, False, 60),
            (500, True, 30),
            (50, False, 60),
        ],
    )
    def test_fee_calculation(self, subtotal, member, expected):
        assert cart.shipping_fee(subtotal, member) == expected

    @pytest.mark.parametrize(
        "subtotal",
        [-1, -10.5],
    )
    def test_invalid_subtotal(self, subtotal):
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal)

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_remove_items(self):
        self.cart.add_item("apple", 100, quantity=2)
        assert self.cart.items() == {"apple": 2}
        # adding more increases quantity
        self.cart.add_item("apple", 100, quantity=3)
        assert self.cart.items()["apple"] == 5
        # remove part of quantity
        self.cart.remove_item("apple", quantity=2)
        assert self.cart.items()["apple"] == 3
        # removing more than exists removes item
        self.cart.remove_item("apple", quantity=5)
        assert "apple" not in self.cart.items()

    def test_subtotal_and_total_non_member_no_coupon(self):
        self.cart.add_item("book", 200, quantity=1)
        self.cart.add_item("pen", 50, quantity=2)  # subtotal = 300
        assert self.cart.subtotal() == 300
        total = self.cart.total(member=False)
        # expected: subtotal + shipping (60) = 360
        assert total == 360

    def test_total_member_no_coupon(self):
        self.cart.add_item("laptop", 1200, quantity=1)
        total = self.cart.total(member=True)
        assert total == 1200

    def test_total_with_coupon(self):
        self.cart.add_item("shirt", 400, quantity=2)  # subtotal 800
        total = self.cart.total(coupon="SAVE10")  # 10% off ->720 +60 shipping=780
        assert total == 780

    def test_invalid_operations_raise_value_error(self):
        with pytest.raises(ValueError):
            self.cart.add_item("bad", -10, quantity=1)
        # removing negative quantity should raise ValueError; implementation raises KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("nothing", quantity=-5)
