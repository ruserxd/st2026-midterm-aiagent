import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),    # no discount
        (50, 100, 0.0),     # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_arguments(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),      # less than 10
        (10, 5),     # exactly 10
        (49, 5),     # just below 50
        (50, 10),    # at 50
        (99, 10),    # just below 100
        (100, 15),   # at 100
        (150, 15),   # above 100
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),          # case-insensitive
        (" SAVE20 ", 20),      # whitespace ignored
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",            # below 1
    "SAVE51",           # above 50
    "SAVEX10",          # wrong prefix
    "10SAVE",           # wrong order
    "" ,                # empty string
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000, False, 0),      # free at exactly 1000
        (999.99, False, 60),   # just below threshold
        (500, True, 30),       # member half fee
        (1200, True, 0),       # over threshold still free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 100, 2)
        self.cart.add_item("banana", 50)
        items = dict(self.cart.items())
        assert items["apple"] == (100, 2)
        assert items["banana"] == (50, 1)

    def test_remove_and_items(self):
        self.cart.add_item("pear", 75, 3)
        self.cart.remove_item("pear", 2)
        assert dict(self.cart.items())["pear"] == (75, 1)
        # remove remaining unit
        self.cart.remove_item("pear")
        assert "pear" not in dict(self.cart.items())

    def test_subtotal_and_total_non_member_no_coupon(self):
        self.cart.add_item("milk", 200, 3)   # 600
        self.cart.add_item("bread", 150)     # 150
        assert self.cart.subtotal() == 750
        assert self.cart.total() == 810  # 750 + shipping 60

    def test_total_with_bulk_discount(self):
        # 120 units of item triggers bulk discount of 15%
        self.cart.add_item("widget", 10, 120)
        expected_subtotal = apply_discount(10 * 120, bulk_discount_percent(120))
        assert self.cart.subtotal() == 1200
        # total includes shipping; subtotal >1000 so free shipping
        assert self.cart.total() == expected_subtotal

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("gem", 200, 1)
        # subtotal 200, member half shipping 30, coupon SAVE10 gives 10% off subtotal
        total = self.cart.total(member=True, coupon="SAVE10")
        discounted_subtotal = apply_discount(200, 10)
        assert total == discounted_subtotal + 30
