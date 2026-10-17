import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # typical case
    (100, 0, 100.0),    # zero percent
    (50, 100, 0.0),     # full discount
])
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def def_test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25 ", 25),
    (" SAVE50 ", 50),
])
def test_parse_coupon_valid(code, result):
    assert parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "  foo  "])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_item_default_quantity(self):
        self.cart.add_item("apple", 0.5)
        assert self.cart.items() == {"apple": (0.5, 1)}

    def test_add_item_with_quantity(self):
        self.cart.add_item("banana", 0.2, 3)
        assert self.cart.items() == {"banana": (0.2, 3)}

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("orange", 1.0, 5)
        # remove less than quantity
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": (1.0, 3)}
        # remove remaining
        self.cart.remove_item("orange", 3)
        assert "orange" not in self.cart.items()

    def test_items_empty(self):
        assert self.cart.items() == {}

    def test_subtotal_calculation(self):
        self.cart.add_item("widget", 10.0, 2)   # 20.0
        self.cart.add_item("gadget", 5.0, 3)   # 15.0
        assert self.cart.subtotal() == 35.0

    def test_total_no_member_no_coupon(self):
        self.cart.add_item("thing", 20.0)
        # subtotal 20 <1000 => shipping 60, no discount
        assert self.cart.total(member=False, coupon=None) == 80.0

    def test_total_with_membership_discount_and_coupon(self):
        self.cart.add_item("bigitem", 800.0)
        # subtotal 800, member gets half shipping 30, plus 15% discount from bulk? quantity default 1 so no bulk.
        # coupon SAVE10 gives additional 10%
        expected = apply_discount(800, 10)   # 720
        expected += shipping_fee(800, True) # 30 -> total 750
        assert self.cart.total(member=True, coupon="SAVE10") == expected
