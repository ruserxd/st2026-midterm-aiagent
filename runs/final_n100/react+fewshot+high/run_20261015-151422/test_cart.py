import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    # Basic discount calculation and rounding.
    assert cart.apply_discount(200, 15) == 170.0
    # Discount with a price that has more than two decimal places.
    expected = round(123.456 * (1 - 0.20), 2)
    assert cart.apply_discount(123.456, 20) == expected


def test_apply_discount_invalid_inputs():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_thresholds():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    # Non-integer should raise ValueError.
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(10.5)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" SAVE30 ") == 30


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEXY")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")  # N must be >=1
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # >50
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")
    with pytest.raises(ValueError):
        cart.parse_coupon("ABCD10")

# ---------- shipping_fee tests ----------

def test_shipping_fee_threshold():
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(999.99, member=False) == 60
    assert cart.shipping_fee(999.99, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- Cart class tests ----------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new_and_existing(self):
        # Add a new item.
        self.cart.add_item("apple", unit_price=1.5, quantity=2)
        assert self.cart.items() == {"apple": 2}
        assert self.cart.subtotal() == round(1.5 * 2, 2)  # no bulk discount
        # Add same item with more units.
        self.cart.add_item("apple", unit_price=1.5, quantity=3)
        assert self.cart.items() == {"apple": 5}
        assert self.cart.subtotal() == round(1.5 * 5, 2)

    def test_add_item_different_price_error(self):
        self.cart.add_item("banana", unit_price=0.9, quantity=1)
        with pytest.raises(ValueError):
            # Attempt to add same name with different price.
            self.cart.add_item("banana", unit_price=1.0, quantity=2)

    def test_add_item_invalid_inputs(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", unit_price=-1.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", unit_price=1.0, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", unit_price=1.0, quantity=-3)

    def test_remove_item(self):
        # Setup two items.
        self.cart.add_item("item1", unit_price=10.0, quantity=5)
        self.cart.add_item("item2", unit_price=20.0, quantity=12)  # bulk discount applies

        # Remove some quantity from item1.
        self.cart.remove_item("item1", quantity=3)
        assert self.cart.items() == {"item1": 2, "item2": 12}
        expected_subtotal = round(10.0 * 2, 2) + cart.apply_discount(20.0 * 12, cart.bulk_discount_percent(12))
        assert self.cart.subtotal() == expected_subtotal

        # Remove more than remaining quantity from item1.
        self.cart.remove_item("item1", quantity=4)
        assert self.cart.items() == {"item2": 12}
        assert self.cart.subtotal() == cart.apply_discount(20.0 * 12, cart.bulk_discount_percent(12))

    def test_remove_nonexistent_item(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("ghost", quantity=1)

    def test_items_is_copy(self):
        self.cart.add_item("copytest", unit_price=5.0, quantity=3)
        items_dict = self.cart.items()
        items_dict["copytest"] = 999
        # Cart's internal state should remain unchanged.
        assert self.cart.items()["copytest"] == 3

    def test_subtotal_with_bulk_discount(self):
        # Add item with bulk discount.
        self.cart.add_item("widget", unit_price=9.99, quantity=12)  # >=10 => 5% discount
        expected = cart.apply_discount(9.99 * 12, cart.bulk_discount_percent(12))
        assert self.cart.subtotal() == round(expected, 2)

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("thing", unit_price=20.0, quantity=12)  # discounted to 228
        expected_sub = cart.apply_discount(20.0 * 12, cart.bulk_discount_percent(12))
        shipping = cart.shipping_fee(expected_sub)
        assert self.cart.total() == round(expected_sub + shipping, 2)

    def test_total_with_coupon(self):
        self.cart.add_item("thing", unit_price=20.0, quantity=12)  # subtotal before coupon 228
        subtotal_before = cart.apply_discount(20.0 * 12, cart.bulk_discount_percent(12))
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = cart.apply_discount(subtotal_before, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("thing", unit_price=20.0, quantity=12)  # subtotal before coupon 228
        subtotal_before = cart.apply_discount(20.0 * 12, cart.bulk_discount_percent(12))
        after_coupon = cart.apply_discount(subtotal_before, 20)  # 20% off via SAVE20
        shipping_fee = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("thing", unit_price=10.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0

# ---------- Additional edge case tests ----------

def test_apply_discount_rounding_behavior():
    # Example where rounding matters.
    price = 10.005
    percent = 0
    expected = round(price, 2)
    assert cart.apply_discount(price, percent) == expected

# End of test_cart.py
