import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---- Tests for apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # Should round to two decimals
    assert apply_discount(199.9999, 10) == pytest.approx(179.99991, rel=1e-5)
    assert apply_discount(199.9999, 10) == round(199.9999 * 0.90, 2)


def test_apply_discount_bounds():
    # percent boundaries
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)


def test_apply_discount_invalid_percent():
    for bad in [-1, 101]:
        with pytest.raises(ValueError):
            apply_discount(100, bad)

# ---- Tests for bulk_discount_percent -------------------------------------------

def test_bulk_discount_percent_tiers():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15


def test_bulk_discount_percent_invalid():
    for bad in [0, -1, 2.5]:
        with pytest.raises(ValueError):
            bulk_discount_percent(bad)

# ---- Tests for parse_coupon -------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("  SAVE50  ") == 50


def test_parse_coupon_invalid():
    invalids = ["", "SAVEX", "SAVE0", "SAVE51", "1234", "   ", "NOTVALID"]
    for code in invalids:
        with pytest.raises(ValueError, msg=f"code {code!r}"):
            parse_coupon(code)

# ---- Tests for shipping_fee -------------------------------------------

def test_shipping_fee_standard():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60


def test_shipping_fee_member():
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(800, member=True) == 30


def test_shipping_fee_free_shipping():
    for subtotal in [1000, 1500]:
        assert shipping_fee(subtotal) == 0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---- Tests for Cart class -------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 100, quantity=2)
        assert self.cart.items() == {"apple": (100, 2)}

    def test_add_item_increment(self):
        self.cart.add_item("banana", 50, quantity=1)
        self.cart.add_item("banana", 50, quantity=3)
        assert self.cart.items()["banana"] == (50, 4)

    def test_remove_item_decrement(self):
        self.cart.add_item("orange", 80, quantity=5)
        self.cart.remove_item("orange", quantity=2)
        assert self.cart.items()["orange"] == (80, 3)

    def test_remove_item_complete_removal(self):
        self.cart.add_item("grape", 30, quantity=3)
        self.cart.remove_item("grape", quantity=3)
        assert "grape" not in self.cart.items()

    def test_subtotal_calculation(self):
        self.cart.add_item("item1", 200, quantity=2)   # 400
        self.cart.add_item("item2", 150, quantity=1)   # 150
        assert self.cart.subtotal() == 550

    def test_total_no_coupon_member(self):
        self.cart.add_item("product", 1000, quantity=1)
        total = self.cart.total(member=True, coupon=None)
        # subtotal 1000 -> free shipping; no discount
        assert total == 1000

    def test_total_with_bulk_and_coupon_member(self):
        # buy 120 units for bulk discount
        self.cart.add_item("bulkitem", 50, quantity=120)   # base subtotal 6000
        coupon_percent = parse_coupon("SAVE10")            # 10%
        total = self.cart.total(member=True, coupon="save10")
        # bulk discount 15% -> 5100; coupon 10% on that -> 4590
        expected_subtotal = 6000 * (1 - 0.15)
        expected_after_coupon = expected_subtotal * (1 - 0.10)
        # shipping free
        assert pytest.approx(total, rel=1e-6) == expected_after_coupon

    def test_total_with_shipping_and_discount(self):
        self.cart.add_item("toy", 200, quantity=3)   # subtotal 600
        total = self.cart.total(member=False, coupon=None)
        # shipping fee 60
        assert total == 660

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_add_item_negative_price_or_qty(self):
        with pytest.raises(ValueError):
            self.cart.add_item("bad", -10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("bad2", 10, quantity=0)

    def test_remove_nonexistent_item(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nothing", quantity=1)
