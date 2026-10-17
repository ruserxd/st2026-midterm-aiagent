import pytest
from cart import (
    apply_discount,
    parse_coupon,
    bulk_discount_percent,
    shipping_fee,
    Cart,
)

def round2(x):
    return round(float(x), 2)

# ---------- Individual function tests ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0
    # rounding check: 99 with 33% discount -> round to two decimals
    assert round2(apply_discount(99, 33)) == 66.03

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-10, 20)

def test_apply_discount_invalid_percent():
    for p in (-1, 101):
        with pytest.raises(ValueError):
            apply_discount(50, p)

# ---- parse_coupon -----

def test_parse_coupon_valid_case_insensitive():
    # Valid coupon codes (case-insensitive, whitespace ignored)
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE10 ") == 10
    # boundary values
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

def test_parse_coupon_invalid():
    invalid_codes = ["", "SAVE0", "SAVETEN", "save51", "SAVEBACK", "123"]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---- bulk_discount_percent -----

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10   # >= 50 gives 10%
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    for q in [0, -1, -10]:
        with pytest.raises(ValueError):
            bulk_discount_percent(q)

# ---- shipping_fee -----

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

def test_shipping_fee_member():
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(499.99, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

def test_shipping_fee_invalid_subtotal():
    for s in [-1, -10]:
        with pytest.raises(ValueError):
            shipping_fee(s)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_empty_cart_total_and_subtotal(self):
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_and_remove_items(self):
        self.cart.add_item("apple", 100, quantity=5)
        # items() returns dict of name: quantity
        assert self.cart.items()["apple"] == 5
        expected_subtotal = round2(100 * 5)  # no bulk discount for qty<10
        assert self.cart.subtotal() == expected_subtotal
        # remove part of quantity
        self.cart.remove_item("apple", quantity=3)
        assert self.cart.items()["apple"] == 2
        expected_after = round2(100 * 2)
        assert self.cart.subtotal() == expected_after
        # removing all should delete item
        self.cart.remove_item("apple", quantity=2)
        assert "apple" not in self.cart.items()

    def test_bulk_discount_in_subtotal(self):
        self.cart.add_item("banana", 200, quantity=10)  # 5% bulk discount
        expected = round2(200 * 10 * (1 - 0.05))
        assert self.cart.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("item", 500, quantity=2)
        # subtotal before coupon: 1000
        # After applying SAVE10 (10%) -> 900; shipping fee 60 for non-member
        total = self.cart.total(coupon="SAVE10")
        assert total == round2(900 + 60)

    def test_total_member_no_shipping_fee(self):
        self.cart.add_item("item", 500, quantity=3)  # subtotal 1500 >1000
        total = self.cart.total(member=True)
        assert total == round2(1500.0)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 100, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_rounding(self):
        # values that produce rounding scenarios
        self.cart.add_item("precise", 33.333, quantity=3)  # 99.999 -> rounded to 100.0
        assert round2(self.cart.subtotal()) == 100.0
        # No coupon, shipping fee applies since subtotal <1000
        assert self.cart.total() == round2(100 + 60)
