import pytest
from math import isclose
import cart

# Helper to compare floats within tolerance

def close(a, b, tol=1e-9):
    return isclose(a, b, abs_tol=tol)

# ---------- apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (5, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (200, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10), ("save20", 20), ("   SaVe5   ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOTC10", " SAVE 10 ", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0.0, False, 60), (500, True, 30), (999.99, False, 60), (1000, False, 0), (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1.0, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, 3)
        assert self.c.items() == {"apple": 3}
        self.c.add_item("apple", 1.0, 2)
        assert self.c.items() == {"apple": 5}

    def test_add_same_name_different_price_raises(self):
        self.c.add_item("banana", 0.5, 1)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 0.6, 2)

    def test_add_invalid_params(self):
        with pytest.raises(ValueError):
            self.c.add_item("orange", -1.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.0, 0)

    def test_remove_item(self):
        self.c.add_item("tshirt", 20.0, 2)
        self.c.remove_item("tshirt", 1)
        assert self.c.items() == {"tshirt": 1}
        self.c.remove_item("tshirt", 1)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent", 1)

    def test_subtotal_with_bulk_discount(self):
        self.c.add_item("apple", 2.0, 12)  # bulk discount 5%
        expected = round(2.0 * 12 * (1 - 0.05), 2)
        assert close(self.c.subtotal(), expected)

    def test_subtotal_rounding_and_empty_cart(self):
        assert self.c.subtotal() == 0
        self.c.add_item("pen", 1.333, 3)
        subtotal = round(1.333 * 3, 2)
        assert close(self.c.subtotal(), subtotal)

    def test_total_without_coupon_and_non_member(self):
        self.c.add_item("book", 30.0, 1)
        total_expected = 30.0 + cart.shipping_fee(30.0, False)
        assert close(self.c.total(), round(total_expected, 2))

    def test_total_with_coupon_and_member(self):
        self.c.add_item("lamp", 50.0, 2)
        subtotal = 100.0
        coupon_percent = cart.parse_coupon("SAVE10")
        discounted = cart.apply_discount(subtotal, coupon_percent)
        shipping = cart.shipping_fee(discounted, True)
        expected_total = round(discounted + shipping, 2)
        assert close(self.c.total(member=True, coupon="SAVE10"), expected_total)

    def test_total_empty_cart(self):
        assert self.c.total() == 0

    def test_total_invalid_coupon_raises(self):
        self.c.add_item("item", 5.0, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")
