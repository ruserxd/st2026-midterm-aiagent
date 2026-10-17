import pytest
import cart

# ---- apply_discount tests ----
@pytest.mark.parametrize(
    "price, percent, result",
    [
        (200, 15, 170.0),           # example from spec
        (100, 0, 100.0),            # no discount
        (50, 100, 0.0),             # full discount
        (123.45, 10, round(123.45*0.90, 2)),
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price, percent",
    [
        (-1, 10),          # negative price
        (100, -5),         # percent < 0
        (100, 105),        # percent > 100
        (100, 50.5),       # non-integer percent but within range (allowed)
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent tests ----
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (0, 0),            # below 10 => 0
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [
        -1,
        0.5,
        "ten",
    ],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon tests ----
@pytest.mark.parametrize(
    "code, percent",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize(
    "code",
    [
        "SAVEXX",           # non-integer N
        "SAVE0",            # out of range (1-50)
        "SAVE51",          # out of range
        "DISCOUNT10",      # wrong prefix
        "  ",              # empty after strip
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee tests ----
@pytest.mark.parametrize(
    "subtotal, member, fee",
    [
        (1000, False, 0),     # free at threshold
        (999.99, False, 60),
        (999.99, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize(
    "subtotal",
    [
        -1,
    ],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart tests ----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_increase_quantity(self):
        self.cart.add_item("banana", 0.5, 2)
        self.cart.add_item("banana", 0.5, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.0, 1)

    def test_remove_item_partial(self):
        self.cart.add_item("grape", 0.3, 5)
        self.cart.remove_item("grape", 2)
        assert self.cart.items() == {"grape": 3}

    def test_remove_item_all(self):
        self.cart.add_item("peach", 1.5, 4)
        self.cart.remove_item("peach", 4)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango", 1)

    def test_subtotal_empty(self):
        assert self.cart.subtotal() == 0.0

    def test_subtotal_with_bulk_discount(self):
        # 10 items => bulk discount 5%
        self.cart.add_item("widget", 20.0, 10)
        expected = round(20.0 * 10 * (1 - 0.05), 2)  # 190.0
        assert self.cart.subtotal() == expected

    def test_total_no_coupons(self):
        self.cart.add_item("item", 100.0, 1)
        # subtotal 100, no discount, shipping 60 => total 160
        assert self.cart.total(member=False) == round(100 + 60, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 200.0, 1)
        # subtotal 200, coupon SAVE10 -> 180, shipping for 180: 60 (not member) but member True so 30
        assert self.cart.total(member=True, coupon="SAVE10") == round(180 + 30, 2)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 50.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
