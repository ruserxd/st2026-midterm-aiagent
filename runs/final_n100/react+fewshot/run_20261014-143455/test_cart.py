import pytest
import cart

# Helper for rounding
from decimal import Decimal, ROUND_HALF_UP

def round2(v):
    return float(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
valid_cases = {
    "SAVE10": 10,
    "save20": 20,
    "  Save30  ": 30,
}
for code, expected in valid_cases.items():
    def _test(code=code, expected=expected):
        assert cart.parse_coupon(code) == expected
    globals()[f"test_parse_coupon_{code.strip().replace(' ','_').lower()}"] = _test

@pytest.mark.parametrize("invalid", ["SAV10", "SAVE0", "SAVE51", "HELLO", " "])  # space-only
def test_parse_coupon_invalid(invalid):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,result", [
    (999.99, False, 60),
    (1000, False, 0),
    (5000, True, 0),   # free for subtotal>=1000 regardless of membership
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # Add items and check quantities
    def test_add_item_basic(self):
        self.cart.add_item("Apple", 2, 3)
        assert self.cart.items() == {"Apple": 3}
        assert round(self.cart.subtotal(), 2) == 6.0

    def test_add_existing_increases_quantity_and_price_match(self):
        self.cart.add_item("Banana", 1.5, 2)
        self.cart.add_item("Banana", 1.5, 3)
        assert self.cart.items() == {"Banana": 5}
        assert round(self.cart.subtotal(), 2) == 7.5

    def test_add_existing_with_different_price_raises(self):
        self.cart.add_item("Orange", 1, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", 1.2, 1)

    @pytest.mark.parametrize("unit_price", [-1, -5])
    def test_add_negative_unit_price(self, unit_price):
        with pytest.raises(ValueError):
            self.cart.add_item("Pear", unit_price, 1)

    @pytest.mark.parametrize("quantity", [0, -2, 2.5])
    def test_add_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("Grape", 3, quantity)

    # Removing items
    def test_remove_item_reduces_qty_and_removes_when_zero(self):
        self.cart.add_item("Mango", 2.0, 4)
        self.cart.remove_item("Mango", 1)
        assert self.cart.items() == {"Mango": 3}
        self.cart.remove_item("Mango", 3)  # should remove completely
        assert self.cart.items() == {}

    def test_remove_more_than_exists_removes_and_no_negative(self):
        self.cart.add_item("Peach", 1.0, 2)
        self.cart.remove_item("Peach", 5)  # removing more than present
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises_keyerror(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("NonExistent", 1)

    # Subtotal with bulk discount
    def test_subtotal_bulk_discount_applied_per_item(self):
        self.cart.add_item("Apple", 10.0, 12)  # qty>=10 ->5%
        expected = round2(10.0 * 12 * (1 - 0.05))
        assert round(self.cart.subtotal(), 2) == expected

    # Total with coupon and shipping
    def test_total_with_coupon_and_member_shipping(self):
        self.cart.add_item("Widget", 100.0, 10)  # qty=10 ->5%
        subtotal = round2(100.0 * 10 * (1 - 0.05))
        coupon_code = "SAVE20"  # 20%
        after_coupon = round2(subtotal * (1 - 0.20))
        shipping = cart.shipping_fee(after_coupon, member=True)
        total_expected = round2(after_coupon + shipping)
        assert self.cart.total(member=True, coupon=coupon_code) == total_expected

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("Item", 50.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
