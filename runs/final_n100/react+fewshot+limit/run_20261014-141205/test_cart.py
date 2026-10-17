import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),            # example
    (100, 0, 100.0),             # no discount
    (50, 100, 0.0),              # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# error cases for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-10, 20),   # negative price
    (50, -5),    # negative percent
    (50, 105),   # >100 percent
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error case: non-positive quantity
@pytest.mark.parametrize("quantity", [0, -3, 1.5, "10"])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",        # N < 1
    "SAVE51",       # N > 50
    "DISCOUNT10",   # wrong prefix
    "save-5",       # negative number
    "" ,            # empty
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# error case: negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_increase_quantity_same_price(self):
        self.cart.add_item("banana", 0.5, 2)
        self.cart.add_item("banana", 0.5, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_error_different_unit_price(self):
        self.cart.add_item("orange", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.5, 2)

    def test_remove_item_partial(self):
        self.cart.add_item("pear", 2.0, 5)
        self.cart.remove_item("pear", 3)
        assert self.cart.items() == {"pear": 2}

    def test_remove_item_exact_and_removal(self):
        self.cart.add_item("peach", 1.2, 4)
        self.cart.remove_item("peach", 4)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("plum", 1)

    def test_subtotal_no_discount(self):
        # quantities below bulk discount thresholds
        self.cart.add_item("itemA", 10.0, 3)   # no discount (qty<10)
        self.cart.add_item("itemB", 5.0, 9)    # qty<10
        assert self.cart.subtotal() == 10*3 + 5*9

    def test_subtotal_with_bulk_discount(self):
        # itemA qty=12 -> 5% discount, itemB qty=55 -> 10%
        self.cart.add_item("itemA", 20.0, 12)
        self.cart.add_item("itemB", 30.0, 55)
        expected_a = round(20*12 * (1-0.05), 2)
        expected_b = round(30*55 * (1-0.10), 2)
        assert self.cart.subtotal() == round(expected_a + expected_b, 2)

    def test_total_no_coupon_or_member(self):
        # subtotal $100, no coupon, non-member -> shipping 60
        self.cart.add_item("bulk", 10.0, 15)   # qty>=10 -> 5% discount
        sub = self.cart.subtotal()
        total_expected = round(sub + cart.shipping_fee(sub, member=False), 2)
        assert self.cart.total() == total_expected

    def test_total_with_coupon_and_member(self):
        # subtotal $200, coupon SAVE20 (20%), member -> shipping half of 60=30
        self.cart.add_item("prod", 10.0, 25)   # qty>=50? no, qty=25 => 5%
        sub = self.cart.subtotal()
        discounted = round(sub - sub * cart.parse_coupon("SAVE20") / 100, 2)
        shipping = cart.shipping_fee(discounted, member=True)
        total_expected = round(discounted + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == total_expected

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
