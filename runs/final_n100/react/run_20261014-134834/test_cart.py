import pytest
import cart

# Tests for apply_discount

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding_and_types():
    # ensure rounding to two decimals
    assert cart.apply_discount(100, 33) == round(100 * (1 - 33/100), 2)
    # price zero works
    assert cart.apply_discount(0, 10) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 20)


def test_apply_discount_invalid_percent():
    for invalid in [-1, 101]:
        with pytest.raises(ValueError):
            cart.apply_discount(100, invalid)

# Tests for bulk_discount_percent

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# Tests for parse_coupon

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe50") == 50


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")

# Tests for shipping_fee

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0


def test_shipping_fee_members():
    # members pay half
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert list(self.cart.items()) == []
        assert self.cart.subtotal() == 0.0

    def test_add_item_basic(self):
        self.cart.add_item("apple", 100, 2)
        assert list(self.cart.items()) == [("apple", (100, 2))]
        assert self.cart.subtotal() == 200

    def test_add_multiple_items_and_quantities(self):
        self.cart.add_item("banana", 50)
        self.cart.add_item("banana", 50, 3)
        # quantities should sum to 4
        assert list(self.cart.items()) == [("banana", (50, 4))]

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("orange", 30, 5)
        self.cart.remove_item("orange", 2)
        assert list(self.cart.items()) == [("orange", (30, 3))]
        # remove remaining quantity
        self.cart.remove_item("orange", 3)
        assert list(self.cart.items()) == []

    def test_remove_nonexistent_or_excess_quantity(self):
        self.cart.add_item("pear", 20, 1)
        with pytest.raises(ValueError):
            self.cart.remove_item("pear", 2)  # removing more than present
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_with_discounts_and_shipping(self):
        self.cart.add_item("widget", 200, 10)
        # bulk discount for 10 -> 5%
        unit_price = cart.apply_discount(200, 5)  # should be 190.0
        expected_subtotal = unit_price * 10
        assert self.cart.subtotal() == expected_subtotal
        # total with member and coupon
        total_no_coup = self.cart.total(member=True)
        shipping_fee_member = cart.shipping_fee(expected_subtotal, member=True)
        assert total_no_coup == expected_subtotal + shipping_fee_member

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("gadget", 300, 1)
        subtotal = self.cart.subtotal()
        # apply coupon SAVE20 -> 20% off on items before shipping
        discounted_items = cart.apply_discount(subtotal, 20)
        expected_total = discounted_items + cart.shipping_fee(discounted_items)
        assert self.cart.total(member=False, coupon="SAVE20") == pytest.approx(expected_total)
        # member should get half shipping
        expected_total_member = discounted_items + cart.shipping_fee(discounted_items, member=True)
        assert self.cart.total(member=True, coupon="SAVE20") == pytest.approx(expected_total_member)
