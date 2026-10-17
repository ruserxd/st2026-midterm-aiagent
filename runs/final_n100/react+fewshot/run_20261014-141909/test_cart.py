import pytest
import cart

# Helper for rounding checks

def approx_equal(a, b):
    return abs(a - b) < 1e-9

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (100.0, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid cases for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (50, -5),
    (60, 120),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (30, 5),
    (50, 10),
    (75, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# invalid qty for bulk_discount_percent
@pytest.mark.parametrize("qty", [0, -1, 3.5, "10"])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupon codes
@pytest.mark.parametrize("code", [
    "SAVEX",      # missing number
    "SAVE0",      # out of range
    "SAVE51",     # out of range
    "INVALID10",
    "",
    123,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# invalid subtotal for shipping_fee
@pytest.mark.parametrize("subtotal", [-10, -1.5, "100"])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
from collections import defaultdict

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 3}
        # Add same item with same price increases quantity
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_existing_price_mismatch(self):
        self.cart.add_item("banana", 50, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 60, 1)

    def test_remove_item(self):
        self.cart.add_item("orange", 80, 4)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": 2}
        # Remove remaining quantity
        self.cart.remove_item("orange", 2)
        assert "orange" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_empty(self):
        assert self.cart.subtotal() == 0.0

    def test_subtotal_with_discounts(self):
        # 10 items, unit price 100 => bulk discount 5%
        self.cart.add_item("item", 100, 10)
        expected = 100 * 10 * (1 - 0.05)  # 950
        assert self.cart.subtotal() == round(expected, 2)
        # 50 items => 10% discount
        self.cart = cart.Cart()
        self.cart.add_item("item", 200, 50)
        expected = 200 * 50 * (1 - 0.10)  # 9000
        assert self.cart.subtotal() == round(expected, 2)

    def test_total_no_coupon(self):
        self.cart.add_item("widget", 400, 3)  # subtotal 1200 no discount
        total = self.cart.total(member=False)
        # shipping free because subtotal >=1000 before coupon
        assert total == 1200.00

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("gadget", 300, 2)  # subtotal 600
        # Apply SAVE10 -> 90% of 600 = 540
        total = self.cart.total(member=False, coupon="SAVE10")
        # shipping fee 60 added => 600
        assert total == 600.00
        # member pays half shipping: expect 570
        total_member = self.cart.total(member=True, coupon="SAVE10")
        assert total_member == 570.00

    def test_total_invalid_coupon(self):
        self.cart.add_item("thing", 200, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
