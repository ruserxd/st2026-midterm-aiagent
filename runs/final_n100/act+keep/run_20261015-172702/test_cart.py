import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Utility helpers ----------

def round2(value: float) -> float:
    return round(float(value), 2)

# ---------- Test apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),  # example from spec
        (100.0, 0, 100.0),   # no discount
        (50.0, 100, 0.0),    # full discount
        (99.99, 10, 89.991),
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == round2(result)

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Test bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,percent",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, percent):
    assert bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Test parse_coupon ----------
@pytest.mark.parametrize(
    "code,percent",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("   SAVE20   ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, percent):
    assert parse_coupon(code) == percent

@pytest.mark.parametrize(
    "code",
    [
        "SAV10",       # missing E
        "SAVE0",       # N < 1
        "SAVE51",      # N > 50
        "DISCOUNT5",   # wrong prefix
        "",            # empty
        "  ",          # whitespace only
    ],
)
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Test shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,fee",
    [
        (0.0, False, 60),
        (500.0, True, 30),
        (999.99, False, 60),
        (1000.0, False, 0),
        (1500.0, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, fee):
    assert shipping_fee(subtotal, member=member) == fee

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Test Cart class functionality ----------

class TestCart:
    def setup_method(self):
        self.cart = Cart()

    # Adding items and subtotal calculation
    def test_add_item_and_subtotal(self):
        # add 5 apples @ $10 each -> no bulk discount (qty <10)
        self.cart.add_item("apple", 10, quantity=5)
        assert self.cart.items() == {"apple": 5}
        assert round2(self.cart.subtotal()) == 50.0

        # add another 7 apples (total 12) -> bulk discount 5%
        self.cart.add_item("apple", 10, quantity=7)
        assert self.cart.items() == {"apple": 12}
        # subtotal: 12*10 =120; 5% off => 114.0
        assert round2(self.cart.subtotal()) == 114.0

    def test_add_item_price_mismatch_error(self):
        self.cart.add_item("banana", 3, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 4, quantity=1)  # price mismatch

    def test_remove_item_and_deletion(self):
        self.cart.add_item("orange", 2, quantity=3)
        self.cart.remove_item("orange", quantity=2)
        assert self.cart.items() == {"orange": 1}
        self.cart.remove_item("orange", quantity=1)
        # item removed entirely
        assert self.cart.items() == {}

    def test_remove_nonexistent_item(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear")

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("widget", 100, quantity=10)  # bulk discount 5%
        subtotal = 100 * 10 * (1 - 0.05)
        expected = round2(subtotal + shipping_fee(subtotal))
        assert round2(self.cart.total()) == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("gadget", 200, quantity=5)  # no bulk discount
        subtotal = 200 * 5
        # apply coupon SAVE20 -> 20% off
        after_coupon = subtotal * (1 - 0.20)
        shipping = shipping_fee(after_coupon, member=True)
        total_expected = round2(after_coupon + shipping)
        assert round2(self.cart.total(member=True, coupon="SAVE20")) == total_expected

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_zero_no_shipping(self):
        assert round2(self.cart.total()) == 0.0
        assert self.cart.items() == {}
        # also verify shipping_fee is not added when empty
        # subtotal zero -> shipping fee would be 60 for non-member, but total should stay 0
        with pytest.raises(ValueError):
            # To confirm shipping_fee handles zero fine; but total should not call it.
            pass

# ---------- Additional edge case tests ----------

@pytest.mark.parametrize(
    "quantity",
    [1, 10, 50, 100],
)
def test_bulk_discount_percent_edge_cases(quantity):
    # ensures correct mapping at thresholds
    expected = {1:0,10:5,50:10,100:15}[quantity]
    assert bulk_discount_percent(quantity) == expected
