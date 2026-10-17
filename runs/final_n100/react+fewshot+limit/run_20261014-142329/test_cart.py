import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (100, -5),  # percent < 0
    (100, 105), # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),   # below 10
    (10, 5),  # exactly 10
    (55, 10), # between 50 and 99
    (120, 15) # >=100
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error cases for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
@pytest.mark.parametrize("code", [
    "SAVE0",            # N < 1
    "SAVE51",           # N > 50
    "DISCOUNT10",       # wrong prefix
    "SAVEXX",           # non-numeric
    "",                 # empty
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# error case shipping_fee negative subtotal
def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Cart functionality tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, 3)
        self.c.add_item("banana", 0.5)
        assert self.c.items() == {"apple": 3, "banana": 1}

    def test_add_existing_increases_quantity(self):
        self.c.add_item("apple", 2.0, 2)
        self.c.add_item("apple", 2.0, 1)
        assert self.c.items() == {"apple": 3}

    def test_add_invalid_unit_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.c.add_item("orange", -1, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1, 0)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1, 2.5)

    def test_add_existing_different_price(self):
        self.c.add_item("apple", 1.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("apple", 1.5, 1)

    def test_remove_item(self):
        self.c.add_item("pear", 3.0, 4)
        self.c.remove_item("pear", 2)
        assert self.c.items() == {"pear": 2}
        self.c.remove_item("pear", 2)  # should remove completely
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexist", 1)

    def test_subtotal_no_discount(self):
        self.c.add_item("item", 10.0, 5)  # qty<10 no discount
        assert self.c.subtotal() == 50.0

    def test_subtotal_with_bulk_discount(self):
        self.c.add_item("item", 20.0, 12)  # qty>=10 =>5%
        expected = round(20.0 * 12 * (1 - 0.05), 2)
        assert self.c.subtotal() == expected

    def test_total_no_coupon_or_member(self):
        self.c.add_item("item", 100.0, 10)  # discount 5%
        subtotal = self.c.subtotal()
        shipping = cart.shipping_fee(subtotal)
        total_expected = round(subtotal + shipping, 2)
        assert self.c.total() == total_expected

    def test_total_with_coupon(self):
        self.c.add_item("item", 50.0, 5)  # no discount
        subtotal = self.c.subtotal()
        coupon_percent = cart.parse_coupon("SAVE20")
        after_coupon = round(subtotal * (1 - coupon_percent/100), 2)
        shipping = cart.shipping_fee(after_coupon)
        total_expected = round(after_coupon + shipping, 2)
        assert self.c.total(coupon="SAVE20") == total_expected

    def test_total_with_member(self):
        self.c.add_item("item", 200.0, 1)  # no discount
        subtotal = self.c.subtotal()
        shipping = cart.shipping_fee(subtotal, member=True)
        total_expected = round(subtotal + shipping, 2)
        assert self.c.total(member=True) == total_expected

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0
