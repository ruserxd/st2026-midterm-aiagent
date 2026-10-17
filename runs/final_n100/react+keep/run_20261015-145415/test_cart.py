import re
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper data -----------
CART_ITEMS = [
    ("Widget", 50, 2),   # subtotal 100
    ("Gadget", 120, 1),  # subtotal 120
]

# ---------- tests for apply_discount ------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),   # example
        (100, 0, 100.0),     # no discount
        (50, 100, 0.0),      # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, abs=1e-2)

# invalid price < 0
@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

# invalid percent outside [0,100]
@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(50, percent)

# ---------- tests for bulk_discount_percent -----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),     # less than 10
        (9, 0),     # boundary
        (10, 5),    # start of tier
        (49, 5),    # just below next tier
        (50, 10),   # new tier
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# invalid quantity non-positive or not int
@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- tests for parse_coupon -----------------
@ pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        ("   SaVe5  ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# invalid format or out of range
@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOSAVE10", "SAVEX", "", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- tests for shipping_fee --------------
@ pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, False, 0),
        (0, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# invalid subtotal negative
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- tests for Cart class -------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_subtotal(self):
        # add a few items and check subtotal calculation
        for name, price, qty in CART_ITEMS:
            self.cart.add_item(name, price, qty)
        expected_subtotal = sum(price * qty for _, price, qty in CART_ITEMS)
        assert self.cart.subtotal() == pytest.approx(expected_subtotal)
        # items returns dict mapping name->quantity
        assert self.cart.items() == {name: qty for name, _, qty in CART_ITEMS}

    def test_remove_item_partial_and_total(self):
        # add 5 units, remove 3 - remaining 2
        self.cart.add_item("Thing", 30, 5)
        self.cart.remove_item("Thing", 3)
        assert self.cart.items() == {"Thing": 2}
        # subtotal should be 60
        assert self.cart.subtotal() == 60

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Nonexistent")

    def test_total_with_coupon_and_member_shipping(self):
        for name, price, qty in CART_ITEMS:
            self.cart.add_item(name, price, qty)
        # cart has subtotal 220; coupon SAVE20 -> discount 44 -> 176
        expected = 176 + 30  # member half shipping
        assert self.cart.total(member=True, coupon="SAVE20") == pytest.approx(expected)

    def test_total_without_items(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        for name, price, qty in CART_ITEMS:
            self.cart.add_item(name, price, qty)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
