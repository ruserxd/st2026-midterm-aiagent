import pytest
import cart

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (123.45, 33, round(123.45 * 0.67, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent -----------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),      # less than 10
        (9, 0),      # just below threshold
        (10, 5),     # at 10
        (49, 5),     # below 50
        (50, 10),    # at 50
        (99, 10),    # below 100
        (100, 15),   # at 100
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2, "ten"],
)
def test_bulk_discount_invalid_args(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "save0",      # below minimum
        "save51",     # above maximum
        "DISCOUNT10", # wrong prefix
        "SAVExx",     # non‑numeric
        "" ,          # empty string
        123,           # not a string
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ---------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 2.0, 3)
        assert self.cart.items() == {"apple": 3}
        # add same item with same price increases quantity
        self.cart.add_item("apple", 2.0, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 2.5)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 3.0, 2)
        with pytest.raises(ValueError):
            # different unit price for same name
            self.cart.add_item("orange", 4.0, 1)

    def test_remove_item(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        # remove remaining quantity
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("plum", 1)

    def test_subtotal_and_bulk_discount(self):
        # 12 apples at $10 each -> bulk discount 5%
        self.cart.add_item("apple", 10.0, 12)
        expected = round(10.0 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_no_items(self):
        assert self.cart.total() == 0.0

    def test_total_with_coupon_and_shipping(self):
        # 10 bananas at $20 each -> bulk discount 5%
        self.cart.add_item("banana", 20.0, 10)
        subtotal = round(20.0 * 10 * (1 - 0.05), 2)  # 190.0
        # apply coupon SAVE10 reduces by 10% -> 171.0
        after_coupon = round(subtotal * 0.90, 2)
        shipping = cart.shipping_fee(after_coupon)
        total_expected = round(after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("kiwi", 5.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="badcode")

    def test_total_member_shipping_free_above_threshold(self):
        # member gets free shipping if subtotal >= 1000 before coupon
        self.cart.add_item("widget", 200.0, 6)  # $1200 total, bulk 5% -> 1140
        assert self.cart.total(member=True) == round(1140 + 0, 2)
