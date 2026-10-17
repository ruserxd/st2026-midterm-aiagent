import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------------------------------------------------------------
# 1. apply_discount
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),           # example from spec
        (100, 0, 100.0),            # no discount
        (50, 100, 0.0),             # full discount
        (99.99, 25, 74.9925),      # value before rounding
    ],
)
def test_apply_discount(price, percent, expected):
    result = apply_discount(price, percent)
    assert isinstance(result, float)
    assert round(result, 2) == round(expected, 2)

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------------------------------------------------------------------------
# 2. bulk_discount_percent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# 3. parse_coupon
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SAVE5  ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVE-1", "SAVEXY", "", "10SAVE"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------------------------------------------------------------------------
# 4. shipping_fee
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# 5. Cart class
# ---------------------------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, quantity=4)
        assert self.cart.items() == {"apple": 4}
        assert self.cart.subtotal() == 10.0

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1, quantity=3)
        self.cart.add_item("banana", 1, quantity=2)
        assert self.cart.items()["banana"] == 5
        assert self.cart.subtotal() == 5.0

    def test_add_item_existing_diff_price(self):
        self.cart.add_item("orange", 3, quantity=2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4, quantity=1)

    @pytest.mark.parametrize("quantity", [0, -2])
    def test_add_item_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 2, quantity=quantity)

    def test_remove_item_partial(self):
        self.cart.add_item("grape", 0.5, quantity=10)  # bulk discount 5%
        self.cart.remove_item("grape", 4)
        assert self.cart.items()["grape"] == 6
        assert round(self.cart.subtotal(), 2) == 2.85

    def test_remove_item_zero_removes(self):
        self.cart.add_item("melon", 10, quantity=1)
        self.cart.remove_item("melon", 1)
        assert "melon" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist", 1)

    def test_total_no_coupon_member(self):
        self.cart.add_item("widget", 100, quantity=5)  # no bulk discount
        total = self.cart.total(member=True)
        assert round(total, 2) == 530.0

    def test_total_with_coupon(self):
        self.cart.add_item("gadget", 200, quantity=10)  # bulk discount 5%
        total = self.cart.total(coupon="SAVE20")
        assert round(total, 2) == 1520.0

    def test_total_empty_no_shipping(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 10)
        with pytest.raises(ValueError):
            self.cart.total(coupon="bad")
