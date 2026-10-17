import re
import pytest
import cart

# ----- apply_discount tests -----

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0


def test_apply_discount_rounding_and_errors():
    # rounding to 2 decimals
    assert cart.apply_discount(99.999, 10) == round(99.999 * 0.9, 2)
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ----- bulk_discount_percent tests -----

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-3)

# ----- parse_coupon tests -----

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("   SaVe5   ") == 5


def test_parse_coupon_invalid_cases():
    # too low or high percentage
    for code in ["SAVE0", "SAVE51"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)
    # non-numeric suffix
    for code in ["SAVExx", "XYZ10"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# ----- shipping_fee tests -----

def test_shipping_fee():
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    # non-member pays full fee
    assert cart.shipping_fee(200, member=False) == 60


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ----- Cart tests -----

class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 2.5, quantity=3)
        self.c.add_item("banana", 1.0)
        assert self.c.items() == {"apple": 3, "banana": 1}

    def test_remove_item_partial_and_total_quantity(self):
        self.c.add_item("apple", 2.5, quantity=4)
        self.c.remove_item("apple", quantity=2)
        assert self.c.items() == {"apple": 2}
        # remove remaining
        self.c.remove_item("apple")
        assert self.c.items() == {}

    def test_subtotal(self):
        self.c.add_item("item1", 10.0, quantity=2)
        self.c.add_item("item2", 5.5)
        # subtotal = 2*10 + 5.5 = 25.5
        assert self.c.subtotal() == pytest.approx(25.5)

    def test_total_member_and_coupon(self):
        self.c.add_item("widget", 100, quantity=5)  # subtotal 500
        # bulk discount for 5 items -> 0%
        # member gets half shipping
        total = self.c.total(member=True)
        expected_subtotal = 500
        shipping = cart.shipping_fee(expected_subtotal, member=True)
        assert total == pytest.approx(expected_subtotal + shipping)

    def test_total_with_coupon_and_bulk(self):
        # add 12 units -> bulk discount 5%
        self.c.add_item("gadget", 20, quantity=12)  # subtotal 240
        coupon_discount = cart.parse_coupon("SAVE10")
        total = self.c.total(coupon=coupon_discount)
        discounted_subtotal = round(240 * (1 - 0.05), 2)
        final_after_coupon = round(discounted_subtotal * (1 - 0.10), 2)
        shipping = cart.shipping_fee(final_after_coupon, member=False)
        assert total == pytest.approx(round(final_after_coupon + shipping, 2))

    def test_total_errors(self):
        # negative quantity on add
        with pytest.raises(ValueError):
            self.c.add_item("err", 10, quantity=-1)
        # remove non-existent item silently? implementation may differ
        # we expect no exception and items unchanged
        self.c.remove_item("missing")
        assert self.c.items() == {}
