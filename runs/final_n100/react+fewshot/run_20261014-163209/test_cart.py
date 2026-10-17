import pytest
import cart

# Helper: round check

def almost_equal(a, b):
    return abs(a-b) < 1e-9

# --- apply_discount tests ---
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---
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
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.7],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    "   Save30   ": 30,
}
@pytest.mark.parametrize("code, expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAV10", "SAVE0", "SAVE51", "save-5", "", None]
@pytest.mark.parametrize("code", invalid_codes)
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
        (1200, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ---
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 0.5, 2)
        assert self.cart.items() == {"apple": 3, "banana": 2}

    def test_add_existing_increases_quantity(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("apple", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 1.5, 1)

    def test_remove_partial_and_total(self):
        self.cart.add_item("pear", 2.0, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango", 1)

    def test_subtotal_no_bulk_discount(self):
        self.cart.add_item("item", 10.0, 5)  # qty<10 -> no discount
        assert self.cart.subtotal() == 50.0

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("widget", 20.0, 12)  # qty>=10 -> 5% discount
        expected = round(20.0 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_no_items(self):
        assert self.cart.total() == 0.0

    def test_total_with_coupon_and_shipping_member(self):
        self.cart.add_item("prod", 200.0, 10)  # qty=10 =>5% bulk discount
        subtotal = self.cart.subtotal()
        coupon_percent = cart.parse_coupon("SAVE20")
        after_coupon = cart.apply_discount(subtotal, coupon_percent)
        shipping = cart.shipping_fee(after_coupon, member=True)
        total_expected = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == total_expected

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("prod", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
