import pytest
from cart import *

# ---------- function apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- function bulk_discount_percent ----------

def test_bulk_discount_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- function parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon("   SaVe20  ") == 20

@ pytest.mark.parametrize("code", ["SAVEx", "10", "SAVE0", "SAVE51", "SAve-5", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- function shipping_fee ----------

def test_shipping_fee_basic():
    assert shipping_fee(1200) == 0
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500) == 60

# member discount half
    assert shipping_fee(999, member=True) == 30
    assert shipping_fee(1500, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_increase_qty_same_price(self):
        self.cart.add_item("banana", 1.0, 2)
        self.cart.add_item("banana", 1.0, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_error_different_price(self):
        self.cart.add_item("orange", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4.0, 2)

    def test_add_item_invalid_unit_price_or_qty(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -5.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 3.0, 0)

    def test_remove_item_reduce_quantity(self):
        self.cart.add_item("grape", 0.2, 10)
        self.cart.remove_item("grape", 4)
        assert self.cart.items() == {"grape": 6}

    def test_remove_item_removes_when_zero(self):
        self.cart.add_item("mango", 5.0, 3)
        self.cart.remove_item("mango", 3)
        assert "mango" not in self.cart.items()

    def test_remove_item_error_not_present(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("kiwi", 1)

    def test_subtotal_empty_cart(self):
        assert self.cart.subtotal() == 0.0

    def test_subtotal_with_bulk_discounts_and_rounding(self):
        # 12 items at $10 each: bulk discount 5% -> price after discount per item =9.5
        self.cart.add_item("item", 10.0, 12)
        expected = round(10.0 * 12 * (1 - 0.05), 2)  # 114.0
        assert self.cart.subtotal() == expected

    def test_total_no_shipping_for_empty_cart(self):
        assert self.cart.total() == 0.0

    def test_total_with_coupon_and_shipping_non_member(self):
        # 5 items at $20 each: no bulk discount, subtotal=100
        self.cart.add_item("widget", 20.0, 5)
        total = self.cart.total(coupon="SAVE10")  # apply 10% coupon -> 90 then +60 shipping =150
        assert total == 150.0

    def test_total_with_coupon_and_shipping_member(self):
        self.cart.add_item("widget", 20.0, 5)
        total = self.cart.total(member=True, coupon="SAVE20")  # 100 -> 80 after coupon, +30 shipping=110
        assert total == 110.0

    def test_total_invalid_coupon(self):
        self.cart.add_item("widget", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_rounding_precision(self):
        # quantity triggers bulk discount but rounding matters
        self.cart.add_item("expensive", 19.99, 10)  # 5% discount
        subtotal = round(19.99 * 10 * (1-0.05), 2)
        total = self.cart.total()
        assert total == subtotal + 60.0

# End of test file
