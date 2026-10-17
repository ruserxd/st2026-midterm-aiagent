import cart
import math
import pytest

# Helper for floating equality

def almost_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# --- apply_discount tests ---
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE5 ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "sava10", "" , "   "]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ---
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_and_subtotal(self):
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_increases_quantity_and_price(self):
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 2}
        # subtotal: 3.0 with no bulk discount
        assert self.cart.subtotal() == 3.0

    def test_add_same_item_with_same_price(self):
        self.cart.add_item("banana", 1.0, 1)
        self.cart.add_item("banana", 1.0, 4)
        assert self.cart.items()["banana"] == 5
        # subtotal: 5.0, no bulk discount
        assert self.cart.subtotal() == 5.0

    def test_add_same_item_with_different_price_raises(self):
        self.cart.add_item("orange", 2.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 3.0, 1)

    def test_remove_item_partial_and_complete_removal(self):
        self.cart.add_item("pear", 2.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items()["pear"] == 2
        # subtotal: 5.0 with no bulk discount for qty 2
        assert self.cart.subtotal() == 5.0
        self.cart.remove_item("pear", 2)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango", 1)

    def test_total_with_coupon_and_shipping(self):
        # add items that trigger bulk discount and subtotal below $1000
        self.cart.add_item("widget", 200, 10)  # qty=10 => 5% off per item
        expected_subtotal = cart.apply_discount(200*10, 5)
        assert math.isclose(self.cart.subtotal(), expected_subtotal, abs_tol=1e-6)
        # coupon SAVE20 -> 20% discount on subtotal after bulk
        total_after_coupon = cart.apply_discount(expected_subtotal, 20)
        shipping = cart.shipping_fee(total_after_coupon, member=False)
        expected_total = round(total_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE20") == expected_total

    def test_member_shopping_and_no_shipping(self):
        # large subtotal to free shipping and member discount
        self.cart.add_item("expensive", 800, 2)  # qty=2 -> no bulk
        # subtotal 1600
        assert self.cart.subtotal() == 1600.0
        assert cart.shipping_fee(1600, member=True) == 0
        # total should be same as subtotal (no coupon)
        assert self.cart.total(member=True) == 1600.0

    def test_invalid_coupon_raises(self):
        self.cart.add_item("item", 10, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_rounding_to_two_decimals(self):
        # create subtotal that leads to many decimal places
        self.cart.add_item("precise", 0.3333, 3)
        # no bulk discount (qty=3), subtotal = 0.9999
        assert math.isclose(self.cart.subtotal(), 1.0, abs_tol=1e-6)  # rounded to 2 decimals
        assert self.cart.total() == 61.0  # shipping 60 + subtotal 1.0
