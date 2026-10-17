import pytest
import cart

# Helper to format floats as rounded to two decimals for comparison
from decimal import Decimal, ROUND_HALF_UP

def round2(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# ---------- Tests for apply_discount ----------

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),   # example
    (100, 0, 100.0),    # no discount
    (100, 100, 0.0),    # full discount
    (123.45, 10, 111.11),  # check rounding: 123.45*0.9=111.105 -> 111.11
])
def test_apply_discount_success(price, percent, expected):
    result = cart.apply_discount(price, percent)
    assert round2(result) == expected

@pytest.mark.parametrize("price,percent", [
    (-1, 10),      # negative price
    (100, -5),     # negative percent
    (100, 105),    # >100 percent
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- Tests for bulk_discount_percent ----------

@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2, "10"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon ----------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE5 ", 5),
])
def test_parse_coupon_success(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",       # missing E
    "SAVE0",       # N out of range
    "SAVE51",      # N > 50
    "SAVE-5",      # negative
    "SAVER",       # no number
    "ABC10",
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Tests for shipping_fee ----------

@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert list(self.cart.items().keys()) == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 2}
        # subtotal: 1.5*2 =3.0 no bulk discount
        assert round2(self.cart.subtotal()) == 3.0

    def test_add_item_existing_increases_quantity(self):
        self.cart.add_item("banana", 0.5, 10)
        self.cart.add_item("banana", 0.5, 5)
        assert self.cart.items() == {"banana": 15}
        # bulk discount for 15 -> 5%
        expected = round2(0.5 * 15 * (1-0.05))
        assert round2(self.cart.subtotal()) == expected

    def test_add_item_price_mismatch_raises(self):
        self.cart.add_item("orange", 0.7, 3)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.8, 1)

    def test_remove_item_partial(self):
        self.cart.add_item("pear", 2.0, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        assert round2(self.cart.subtotal()) == round2(2*2.0)

    def test_remove_item_entirely(self):
        self.cart.add_item("kiwi", 1.0, 3)
        self.cart.remove_item("kiwi", 3)
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_total_without_coupon_or_member(self):
        # items: 2 apples at $1 each (no bulk), shipping 60
        self.cart.add_item("apple", 1.0, 2)
        expected = round2(2*1.0 + 60)
        assert round2(self.cart.total()) == expected

    def test_total_with_member_no_coupon(self):
        # subtotal: $200, shipping 30 (member)
        self.cart.add_item("item", 100.0, 2)
        expected = round2(200 + 30)  # member half shipping
        assert round2(self.cart.total(member=True)) == expected

    def test_total_with_coupon(self):
        # subtotal: $100, coupon 20% => 80, shipping 60
        self.cart.add_item("item", 50.0, 2)
        total = self.cart.total(coupon="SAVE20")
        assert round2(total) == round2(80 + 60)

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0

# Run a quick sanity check: adding many items triggers bulk discount
@pytest.mark.parametrize("quantity,expected_discount", [
    (9, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_on_cart(quantity, expected_discount):
    c = cart.Cart()
    c.add_item("bulk", 1.0, quantity)
    # subtotal should reflect bulk discount
    expected_subtotal = round2(1.0 * quantity * (1 - expected_discount/100))
    assert round2(c.subtotal()) == expected_subtotal
