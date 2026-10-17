import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_extremes(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_negative_qty_raises(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon(" SAVE5") == 5

@pytest.mark.parametrize(
    "code",
    ["SA V10", "SAVEX", "SAVE0", "SAVE51", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ------------------------------------------------------

def test_shipping_fee_non_member():
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

@pytest.mark.parametrize(
    "subtotal, expected",
    [(50, 30), (0, 30)],
)
def test_shipping_fee_member(subtotal, expected):
    assert shipping_fee(subtotal, member=True) == expected

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initial_empty_subtotals_and_items(self):
        assert self.cart.subtotal() == 0.0
        assert self.cart.items() == {}

    def test_add_item_basic(self):
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple": 2}
        assert self.cart.subtotal() == 2.0

    def test_add_existing_increases_quantity(self):
        self.cart.add_item("banana", 0.5, 3)
        self.cart.add_item("banana", 0.5, 4)
        assert self.cart.items() == {"banana": 7}
        assert self.cart.subtotal() == 3.5

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("orange", 0.8, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.9, 2)

    @ pytest.mark.parametrize("price", [-1, -5])
    def test_add_negative_price_raises(self, price):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", price, 1)

    @ pytest.mark.parametrize("qty", [0, -3])
    def test_add_invalid_quantity_raises(self, qty):
        with pytest.raises(ValueError):
            self.cart.add_item("grape", 2.0, qty)

    def test_remove_item_basic(self):
        self.cart.add_item("mango", 1.5, 3)
        self.cart.remove_item("mango", 1)
        assert self.cart.items() == {"mango": 2}

    def test_remove_item_to_zero_removes_entry(self):
        self.cart.add_item("peach", 0.75, 2)
        self.cart.remove_item("peach", 2)
        assert "peach" not in self.cart.items()

    def test_remove_nonexistent_raises_keyerror(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist", 1)

    def test_subtotal_bulk_discount(self):
        self.cart.add_item("widget", 10.0, 12)   # bulk discount 5%
        expected = apply_discount(120.0, 5)
        assert round(self.cart.subtotal(), 2) == round(expected, 2)

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("book", 20.0, 1)
        after_coupon = apply_discount(20.0, 10)
        shipping = shipping_fee(after_coupon)
        expected_total = round(after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("pen", 5.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
