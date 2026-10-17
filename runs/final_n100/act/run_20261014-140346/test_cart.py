import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- helper constants ----------
PRICE = 200.0
DISCOUNT_PERCENT = 15
EXPECTED_DISCOUNTED_PRICE = 170.0

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100, 10, 90.0),
        (200.5, 25, 150.38),  # 200.5*0.75 = 150.375 rounded
        (0, 50, 0.0),
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (25, 5),
        (50, 10),
        (75, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
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
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "save0",
        "SAVE51",
        "DISCOUNT10",
        "  ",
        "savelow",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initially_empty_subtotal_and_total(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_increases_quantity_and_subtotal(self):
        self.cart.add_item("apple", 100, 5)
        # bulk discount: quantity 5 => 0%
        assert self.cart.subtotal() == 500.00
        self.cart.add_item("apple", 100, 6)  # now quantity 11 -> 5% discount
        # new subtotal: 1100 * 0.95 = 1045 rounded
        assert self.cart.subtotal() == round(1100 * 0.95, 2)

    def test_add_item_same_price_error(self):
        self.cart.add_item("banana", 50, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 60, 1)

    def test_remove_item_and_automatic_removal(self):
        self.cart.add_item("pear", 30, 2)
        self.cart.remove_item("pear", 1)
        assert self.cart.items() == {"pear": 1}
        self.cart.remove_item("pear", 1)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist", 1)

    def test_total_with_coupon_and_shipping(self):
        # add items to exceed shipping threshold after discount
        self.cart.add_item("itemA", 200, 3)  # subtotal 600
        coupon_percent = parse_coupon("SAVE10")
        # subtotal after coupon: 540
        expected_after_coupon = apply_discount(600, coupon_percent)
        shipping = shipping_fee(expected_after_coupon, member=False)
        total_expected = round(expected_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_member_ships_half(self):
        self.cart.add_item("itemB", 100, 1)  # subtotal 100
        expected = apply_discount(100, parse_coupon("SAVE5"))  # 95
        shipping = shipping_fee(expected, member=True)
        assert self.cart.total(member=True, coupon="SAVE5") == round(expected + shipping, 2)

    def test_total_empty_no_shipping(self):
        assert self.cart.total(coupon="SAVE10") == 0

    def test_add_item_invalid_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("bad", -5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("bad", 5, 0)
