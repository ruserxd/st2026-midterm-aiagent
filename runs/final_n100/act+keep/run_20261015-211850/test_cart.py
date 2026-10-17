import pytest
import cart
from math import isclose

# ---------- Utility helpers for parameterized tests ----------

# Helper to round floats in expected values if needed

# -----------------------------------------------------------------

# Tests for apply_discount
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full free
        (123.45, 12, 108.636),     # round to 2 decimals -> 108.64
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == pytest.approx(round(result, 2))

# Edge cases for errors in apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),   # less than 10
        (9, 0),
        (10, 5),
        (25, 5),
        (50, 10),
        (75, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Edge cases: negative or zero quantity
@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_negative_or_zero_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("quantity", [3.5, "a string", None])
def test_bulk_discount_nonint_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   Save5  ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupon codes raise ValueError
@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "NOTACODE",
    "SAVE-5",
    "SAVEX10",
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),          # below free threshold
        (999.99, False, 60),     # just under
        (1000, False, 0),        # free shipping
        (1500, False, 0),
        (500, True, 30),         # member half
        (1200, True, 0),         # free for member too
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Edge cases: negative subtotal raises ValueError
@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_initially(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_basic(self):
        self.c.add_item("apple", 1.5, quantity=3)
        assert self.c.items() == {"apple": 3}
        # subtotal = 1.5 * 3 = 4.5, no bulk discount yet
        assert self.c.subtotal() == pytest.approx(4.5)

    def test_add_item_increases_quantity(self):
        self.c.add_item("banana", 0.8, quantity=2)
        self.c.add_item("banana", 0.8, quantity=3)
        assert self.c.items() == {"banana": 5}
        # bulk discount for qty 5 -> 0%
        assert self.c.subtotal() == pytest.approx(0.8 * 5)

    def test_add_item_wrong_price_raises(self):
        self.c.add_item("orange", 1.0, quantity=2)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.2, quantity=1)

    def test_remove_item_basic(self):
        self.c.add_item("pear", 2.0, quantity=4)
        self.c.remove_item("pear", quantity=2)
        assert self.c.items() == {"pear": 2}
        # subtotal still 4.0
        assert self.c.subtotal() == pytest.approx(4.0)

    def test_remove_item_removes_entire(self):
        self.c.add_item("mango", 3.0, quantity=1)
        self.c.remove_item("mango", quantity=1)
        assert self.c.items() == {}
        assert self.c.subtotal() == pytest.approx(0.0)

    def test_remove_more_than_exists_removes_and_no_negative(self):
        self.c.add_item("kiwi", 2.5, quantity=3)
        # Removing 5 should drop to 0 and remove the key
        self.c.remove_item("kiwi", quantity=5)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent")

    def test_subtotal_with_bulk_discount(self):
        # 12 apples at $1 each -> bulk discount 5%
        self.c.add_item("apple", 1.0, quantity=12)
        expected = 12 * 1.0 * (1 - 0.05)  # 11.4
        assert self.c.subtotal() == pytest.approx(expected, rel=1e-9)

    def test_total_without_coupon_member(self):
        self.c.add_item("widget", 200, quantity=3)  # subtotal = 600
        # no coupon: shipping fee 60 (not member)
        assert self.c.total() == pytest.approx(600 + 60)

    def test_total_with_coupon(self):
        self.c.add_item("gadget", 100, quantity=5)  # subtotal = 500
        # coupon SAVE10 -> 10% off on 500 => 450
        # shipping fee for 450 (non‑member) is 60
        assert self.c.total(coupon="SAVE10") == pytest.approx(510)

    def test_total_with_invalid_coupon_raises(self):
        self.c.add_item("thing", 50, quantity=2)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_total_member_discount_and_shipping(self):
        # subtotal $2000 -> free shipping
        self.c.add_item("expensive", 500, quantity=4)  # subtotal = 2000
        assert self.c.total(member=True) == pytest.approx(2000)

    def test_total_with_member_and_coupon(self):
        self.c.add_item("item", 250, quantity=5)  # subtotal = 1250
        # coupon SAVE20 -> 20% off => 1000
        # shipping free for member (since >=1000 after coupon)
        assert self.c.total(member=True, coupon="SAVE20") == pytest.approx(1000)

    def test_total_empty_cart_costs_zero_no_shipping(self):
        assert self.c.total() == 0.0
