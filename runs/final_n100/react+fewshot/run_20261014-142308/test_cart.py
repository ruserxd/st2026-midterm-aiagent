import pytest
import cart

# Helper for floating point equality

def assert_close(a, b, msg=None):
    assert abs(a - b) <= 0.01, msg or f"{a} != {b}"

# ---------- apply_discount ----------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Value errors
@pytest.mark.parametrize("price, percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error on non-positive quantity
@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    ("  SaVe50", 50),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

# error cases
@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "foo10", "SAVEB"])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# negative subtotal error
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # add_item and items
    def test_add_and_items(self):
        self.cart.add_item("apple", 0.5, 3)
        assert self.cart.items() == {"apple": 3}
        # adding same item increases quantity
        self.cart.add_item("apple", 0.5, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_errors(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1, 0)
        # mismatched unit price for existing item
        self.cart.add_item("orange", 2.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 3.0, 1)

    # remove_item
    def test_remove(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        self.cart.remove_item("pear", 2)  # should remove item
        assert self.cart.items() == {}

    def test_remove_errors(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    # subtotal calculation with bulk discounts
    def test_subtotal_bulk(self):
        # quantity 9 => no discount
        self.cart.add_item("pen", 2.0, 9)
        assert_close(self.cart.subtotal(), 18.0, "no bulk for <10")
        # quantity 12 => 5% off
        self.cart.remove_item("pen", 9)  # clear previous
        self.cart.add_item("pen", 2.0, 12)
        expected = round(2.0 * 12 * (1 - 0.05), 2)
        assert_close(self.cart.subtotal(), expected, "5% bulk")
        # quantity 50 => 10%
        self.cart.remove_item("pen", 12)
        self.cart.add_item("pen", 2.0, 50)
        expected = round(2.0 * 50 * (1 - 0.10), 2)
        assert_close(self.cart.subtotal(), expected, "10% bulk")
        # quantity 100 => 15%
        self.cart.remove_item("pen", 50)
        self.cart.add_item("pen", 2.0, 100)
        expected = round(2.0 * 100 * (1 - 0.15), 2)
        assert_close(self.cart.subtotal(), expected, "15% bulk")

    # total with coupon and shipping
    def test_total_no_coupon_no_member(self):
        self.cart.add_item("book", 30, 2)  # $60 subtotal
        # no discount, shipping = 60 because subtotal < 1000
        expected = round(60 + 60, 2)
        assert_close(self.cart.total(), expected)

    def test_total_coupon_member(self):
        self.cart.add_item("item", 200, 1)  # $200 subtotal
        # coupon SAVE20 => 20% off
        total_after_discount = round(200 * (1 - 0.20), 2)
        shipping = cart.shipping_fee(total_after_discount, member=True)
        expected = round(total_after_discount + shipping, 2)
        assert_close(self.cart.total(member=True, coupon="SAVE20"), expected)

    def test_total_errors_coupon(self):
        self.cart.add_item("widget", 10, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    # empty cart
    def test_empty_cart_costs_zero(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0
