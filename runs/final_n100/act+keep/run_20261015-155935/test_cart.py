import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_invalid_quantity(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon("  SAVE50  ") == 50

@ pytest.mark.parametrize(
    "code",
    ["SAVEX", "123", "", "SAVE0", "SAVE51"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_and_remove_item(self):
        self.cart.add_item("apple", 1.5, quantity=3)
        assert self.cart.items() == {"apple": 3}
        self.cart.add_item("apple", 1.5, quantity=2)
        assert self.cart.items() == {"apple": 5}
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 2.0, quantity=1)

    def test_remove(self):
        self.cart.add_item("banana", 0.8, quantity=4)
        self.cart.remove_item("banana", 2)
        assert self.cart.items() == {"banana": 2}
        self.cart.remove_item("banana", 5)
        assert "banana" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_no_discount(self):
        self.cart.add_item("widget", 10, quantity=5)
        assert self.cart.subtotal() == 50.0

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("gadget", 20, quantity=12)
        expected = round(20 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("item", 200, quantity=3)
        total_before = 600
        coupon_discounted = round(total_before * (1 - 0.10), 2)
        shipping = shipping_fee(coupon_discounted, member=False)
        expected_total = round(coupon_discounted + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_no_shipping_on_empty(self):
        assert self.cart.total() == 0

    @ pytest.mark.parametrize("member", [True, False])
    def test_member_shipping_discount(self, member):
        self.cart.add_item("big", 500, quantity=3)
        assert self.cart.total(member=member) == round(1500, 2)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.add_item("foo", 10, quantity=1)
            self.cart.total(coupon="BAD")
