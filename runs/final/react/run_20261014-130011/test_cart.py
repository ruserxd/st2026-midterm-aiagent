import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (123.45, 5, 117.27),      # rounding check: 123.45*0.95=117.2775 => 117.28? spec says round to 2 decimals.
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    ["abc", None, -5, 105, 150],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),     # less than 10
        (10, 5),    # threshold 10
        (49, 5),    # just below 50
        (50, 10),   # threshold 50
        (99, 10),   # just below 100
        (100, 15),  # threshold 100
        (150, 15),  # above 100
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        (" SAVE30", 30),
        ("sAvE5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # below range
        "SAVE51",         # above range
        "SAV10",          # missing letter S
        "save-5",         # negative number
        "12345",          # no SAVE prefix
        "",               # empty string
    ],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),   # threshold free for all
        (1500, True, 0),    # above threshold
        (999.99, False, 60),# just below threshold
        (200, True, 30),    # member gets half
        (0, False, 60),     # zero subtotal still charges shipping
    ],
)
def test_shipping_fee_valid(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 60.0  # shipping only, non-member

    def test_add_item_basic(self):
        self.cart.add_item("apple", 100)
        assert self.cart.items() == {"apple": (100, 1)}
        assert self.cart.subtotal() == 100.0
        assert self.cart.total() == 160.0  # 100 + shipping 60

    def test_add_item_multiple(self):
        self.cart.add_item("banana", 200, quantity=3)
        assert self.cart.items() == {"banana": (200, 3)}
        assert self.cart.subtotal() == 600.0
        # subtotal 600 < 1000 => shipping 60
        assert self.cart.total(member=True) == 630.0

    def test_add_existing_item_increments_quantity(self):
        self.cart.add_item("apple", 50, quantity=2)
        self.cart.add_item("apple", 50, quantity=3)
        assert self.cart.items()["apple"] == (50, 5)

    def test_remove_item_partial(self):
        self.cart.add_item("orange", 80, quantity=4)
        self.cart.remove_item("orange", quantity=2)
        assert self.cart.items()["orange"] == (80, 2)
        assert self.cart.subtotal() == 160.0

    def test_remove_item_exact(self):
        self.cart.add_item("pear", 120, quantity=2)
        self.cart.remove_item("pear")  # default quantity=1
        assert self.cart.items()["pear"] == (120, 1)

    def test_remove_more_than_present_deletes(self):
        self.cart.add_item("melon", 300, quantity=1)
        self.cart.remove_item("melon", quantity=5)  # should remove item completely
        assert "melon" not in self.cart.items()

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("toy", 500, quantity=2)  # subtotal 1000
        # free shipping
        total = self.cart.total(member=True, coupon="SAVE20")
        # subtotal after discount: 1000 * (1-0.20)=800
        assert total == 800.0

    def test_total_discount_edge_cases(self):
        # quantity 10 should trigger bulk discount of 5%
        self.cart.add_item("book", 200, quantity=10)
        expected_subtotal = 200 * 10  # 2000
        expected_bulk_disc = expected_subtotal * 0.05
        subtotal_after_bulk = expected_subtotal - expected_bulk_disc
        total = self.cart.total()
        assert round(total,2) == round(subtotal_after_bulk + 60,2)

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
