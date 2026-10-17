import pytest
import cart

# ---------- apply_discount -------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (123.45, 20, 98.76),       # rounding to two decimals
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases: invalid arguments raise ValueError
@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (250, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -3, 1.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon --------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "SAVE-5", "ABC"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee --------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -----------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.00, 3)
        self.cart.add_item("banana", 0.50, 2)
        assert self.cart.items() == {"apple": 3, "banana": 2}

    def test_add_existing_increases_quantity_and_price_check(self):
        self.cart.add_item("orange", 0.80, 1)
        # same price: should increase quantity
        self.cart.add_item("orange", 0.80, 4)
        assert self.cart.items() == {"orange": 5}
        # different price: raises ValueError
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.90, 1)

    def test_remove_items_and_auto_removal(self):
        self.cart.add_item("pear", 2.00, 5)
        # remove fewer than total
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 3}
        # remove remaining, item should disappear
        self.cart.remove_item("pear", 3)
        assert self.cart.items() == {}
        # removing non-existent item raises KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_no_discounts(self):
        self.cart.add_item("muffin", 3.00, 2)  # quantity <10 - no bulk discount
        assert self.cart.subtotal() == 6.0

    def test_subtotal_with_bulk_discount(self):
        # 12 items = 5% bulk discount
        self.cart.add_item("bagel", 1.50, 12)
        expected = round(1.50 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_without_coupon_or_member(self):
        # subtotal less than 1000, non-member => +60 shipping
        self.cart.add_item("candy", 10.00, 5)  # no bulk discount
        subtotal = 50.0
        total_expected = round(subtotal + cart.shipping_fee(subtotal), 2)
        assert self.cart.total() == total_expected

    def test_total_with_coupon_and_member(self):
        # subtotal 2500, member => free shipping
        self.cart.add_item("gift", 500.00, 5)  # 5 items - no bulk discount
        subtotal = 2500.0
        coupon_percent = cart.parse_coupon("SAVE10")
        after_discount = round(subtotal * (1 - coupon_percent / 100), 2)
        total_expected = round(after_discount + cart.shipping_fee(after_discount, member=True), 2)
        assert self.cart.total(member=True, coupon="SAVE10") == total_expected

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("toy", 20.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_empty_cart_costs_zero_and_no_shipping(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0
