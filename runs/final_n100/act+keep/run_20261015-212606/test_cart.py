import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- tests for apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 25, 92.0875),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == round(expected, 2)

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- tests for bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
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
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- tests for parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [("SAVE10", 10), ("save25", 25), (" SAVE50 ", 50)],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEX", ""] )

def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- tests for shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
        (300, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- tests for Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 100, 2)
        self.cart.add_item("banana", 200)
        assert self.cart.items() == {"apple": 2, "banana": 1}

    def test_add_existing_increases_quantity(self):
        self.cart.add_item("apple", 100, 2)
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items()["apple"] == 5

    def test_add_item_mismatch_price_raises(self):
        self.cart.add_item("apple", 100, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 90, 1)

    def test_remove_item_decreases_and_removes(self):
        self.cart.add_item("orange", 50, 4)
        self.cart.remove_item("orange", 2)
        assert self.cart.items()["orange"] == 2
        self.cart.remove_item("orange", 2)
        assert "orange" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear")

    def test_subtotal_with_bulk_discount(self):
        # 10 items at 100 each: bulk discount 5%
        self.cart.add_item("widget", 100, 10)
        expected = round(100 * 10 * 0.95, 2)  # 950
        assert self.cart.subtotal() == expected

    def test_subtotal_empty(self):
        assert self.cart.subtotal() == 0

    def test_total_no_coupon_or_shipping_on_empty(self):
        assert self.cart.total() == 0

    def test_total_with_discount_and_shipping(self):
        # 2 items: 100 each, subtotal 200
        self.cart.add_item("item", 100, 2)
        total = self.cart.total(member=False, coupon="SAVE10")  # 10% off -> 180, +60 shipping = 240
        assert round(total, 2) == 240.0

    def test_total_member_free_shipping(self):
        self.cart.add_item("item", 100, 11)  # subtotal 1100 > 1000
        total = self.cart.total(member=True)
        # no discount, shipping free
        assert round(total, 2) == 1100.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 50, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
