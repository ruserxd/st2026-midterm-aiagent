import pytest
import cart

# Helper functions for parameterized tests

def assert_raises(exc_type, func, *args, **kwargs):
    with pytest.raises(exc_type):
        func(*args, **kwargs)

class TestApplyDiscount:
    def test_valid_discount(self):
        assert cart.apply_discount(200, 15) == 170.0

    def test_rounding(self):
        # Ensure rounding to two decimals
        assert cart.apply_discount(100.567, 10) == round(100.567 * 0.9, 2)

    def test_invalid_price(self):
        assert_raises(ValueError, cart.apply_discount, -5, 10)

    def test_invalid_percent_low(self):
        assert_raises(ValueError, cart.apply_discount, 50, -1)

    def test_invalid_percent_high(self):
        assert_raises(ValueError, cart.apply_discount, 50, 101)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize(
        "quantity, expected",
        [
            (9, 0),
            (10, 5),
            (49, 5),
            (50, 10),
            (99, 10),
            (100, 15),
            (150, 15),
        ],
    )
    def test_bulks(self, quantity, expected):
        assert cart.bulk_discount_percent(quantity) == expected

    def test_invalid_quantity_zero(self):
        assert_raises(ValueError, cart.bulk_discount_percent, 0)

    def test_negative_quantity(self):
        assert_raises(ValueError, cart.bulk_discount_percent, -5)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code, expected",
        [
            ("SAVE10", 10),
            ("save20", 20),
            (" SAVE30 ", 30),
        ],
    )
    def test_valid(self, code, expected):
        assert cart.parse_coupon(code) == expected

    @pytest.mark.parametrize(
        "invalid_code",
        ["SAVE", "SAV10", "save0", "save51", "foo10", " SAVE -5 "]
    )
    def test_invalid(self, invalid_code):
        assert_raises(ValueError, cart.parse_coupon, invalid_code)

class TestShippingFee:
    def test_free_shipping_above_limit(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500.50) == 0

    def test_regular_shipping_non_member(self):
        assert cart.shipping_fee(999.99) == 60

    def test_half_for_members(self):
        assert cart.shipping_fee(500, member=True) == 30

    def test_invalid_subtotal_negative(self):
        assert_raises(ValueError, cart.shipping_fee, -10)

class TestCartClass:
    def test_init_and_items(self):
        c = cart.Cart()
        assert c.items() == []

    def test_add_item_single(self):
        c = cart.Cart()
        c.add_item("apple", 1.00, quantity=3)
        assert c.items() == [{"name": "apple", "unit_price": 1.0, "quantity": 3}]

    def test_add_same_item_updates_quantity(self):
        c = cart.Cart()
        c.add_item("banana", 0.5)
        c.add_item("banana", 0.5, quantity=2)
        assert c.items() == [{"name": "banana", "unit_price": 0.5, "quantity": 3}]

    def test_remove_item(self):
        c = cart.Cart()
        c.add_item("orange", 0.8, quantity=4)
        c.remove_item("orange", quantity=2)
        assert c.items() == [{"name": "orange", "unit_price": 0.8, "quantity": 2}]

    def test_remove_more_than_exists(self):
        c = cart.Cart()
        c.add_item("grape", 1.5, quantity=3)
        # removing more than present should delete the item entirely
        c.remove_item("grape", quantity=5)
        assert c.items() == []

    def test_subtotal(self):
        c = cart.Cart()
        c.add_item("milk", 2.0, quantity=3)
        c.add_item("bread", 1.5)
        # subtotal: 3*2 + 1*1.5 = 7.5
        assert c.subtotal() == 7.5

    def test_total_without_member_or_coupon(self):
        c = cart.Cart()
        c.add_item("pen", 1.25, quantity=4)   # subtotal 5.0
        # no discount, shipping 60 => total 65
        assert c.total() == 65.0

    def test_total_with_member_discount_and_coupon(self):
        c = cart.Cart()
        c.add_item("notebook", 10.0, quantity=1)
        # subtotal 10.0; member discount 5% => 9.5; shipping free (>=1000? no) so 60
        # apply coupon SAVE20 => 20% off 9.5 = 7.6; total = 7.6 + 60 = 67.6
        assert c.total(member=True, coupon="SAVE20") == pytest.approx(67.6)
