import pytest
import cart

# ---------- apply_discount ----------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),   # example from spec
        (100, 50, 50.0),    # simple half
        (123.45, 33, round(123.45 * (1 - 0.33), 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [
        (-10, 20),          # negative price
        (100, -5),          # percent too low
        (100, 105),         # percent too high
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),      # below 10
        (10, 5),     # boundary for 5%
        (49, 5),     # just below 50
        (50, 10),    # boundary for 10%
        (99, 10),    # just below 100
        (100, 15),   # boundary for 15%
        (150, 15),
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [
        (-1, ),          # negative quantity
        (0, ),           # zero quantity
        (3.5, ),         # non-integer
    ],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon --------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),          # whitespace trimmed, case-insensitive
        ("SaVe05", 5),
        ("save50", 50),            # upper boundary
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # below minimum
        "SAVE51",         # above maximum
        "DISCOUNT10",     # wrong prefix
        "SAVEABC",        # non-numeric suffix
        "",               # empty string
        "  ",             # only whitespace
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee --------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),   # free at threshold
        (1500, True, 0),    # free for any subtotal >= 1000
        (500, True, 30),
    ],
)
def test_shipping_fee_valid(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [
        -10,
        -0.01,
    ],
)
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal, member=False)

# ---------- Cart class -----------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # items() should initially be empty
    def test_items_initially_empty(self):
        assert self.cart.items() == {}

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple": (1.0, 3)}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.5, quantity=2)
        self.cart.add_item("banana", 0.5, quantity=4)
        assert self.cart.items() == {"banana": (0.5, 6)}

    def test_add_item_existing_different_price(self):
        self.cart.add_item("orange", 1.2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.3)

    @pytest.mark.parametrize(
        "unit_price, quantity",
        [
            (-5, 1),         # negative price
            (1.0, 0),        # zero quantity
            (2.5, -3),       # negative quantity
            (2.0, 1.5),      # non-integer quantity
        ],
    )
    def test_add_item_invalid(self, unit_price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("item", unit_price, quantity)

    def test_remove_item_not_present(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_remove_item_partial(self):
        self.cart.add_item("cherry", 0.3, quantity=5)
        self.cart.remove_item("cherry", quantity=2)
        assert self.cart.items() == {"cherry": (0.3, 3)}

    def test_remove_item_exact(self):
        self.cart.add_item("date", 0.8, quantity=4)
        self.cart.remove_item("date", quantity=4)
        # item should be removed entirely
        assert "date" not in self.cart.items()

    def test_remove_item_more_than_present(self):
        self.cart.add_item("fig", 1.5, quantity=2)
        self.cart.remove_item("fig", quantity=5)  # more than existing
        assert "fig" not in self.cart.items()

    def test_subtotal_single_item(self):
        self.cart.add_item("grape", 0.25, quantity=8)
        assert self.cart.subtotal() == pytest.approx(2.0)

    def test_subtotal_multiple_items(self):
        self.cart.add_item("ham", 5.0, quantity=1)
        self.cart.add_item("iguana", 3.5, quantity=2)  # unusual name
        expected = 5.0*1 + 3.5*2
        assert self.cart.subtotal() == pytest.approx(expected)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_no_coupon_non_member(self):
        # subtotal $200, no coupon, non-member shipping = 60
        self.cart.add_item("jelly", 50.0, quantity=4)
        expected = 200 + 60
        assert self.cart.total() == pytest.approx(expected)

    def test_total_no_coupon_member(self):
        # subtotal $200, member shipping = 30
        self.cart.add_item("kale", 50.0, quantity=4)
        expected = 200 + 30
        assert self.cart.total(member=True) == pytest.approx(expected)

    def test_total_with_coupon(self):
        # subtotal $300, coupon SAVE10 gives 10% off -> 270, shipping 60
        self.cart.add_item("lemon", 75.0, quantity=4)
        total = self.cart.total(coupon="SAVE10")
        assert total == pytest.approx(270 + 60)  # 330

    def test_total_with_coupon_member(self):
        # subtotal $300, coupon SAVE20 gives 20% off -> 240, shipping 30 (member)
        self.cart.add_item("mango", 75.0, quantity=4)
        total = self.cart.total(member=True, coupon="SAVE20")
        assert total == pytest.approx(240 + 30)  # 270

    def test_total_invalid_coupon(self):
        self.cart.add_item("nectarine", 10.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_rounding(self):
        # subtotal $199.99, coupon SAVE5 gives 5% off -> 189.9905, round to 2 decimals = 189.99
        # shipping fee 60 (non-member) -> total 249.99
        self.cart.add_item("orange", 49.9975, quantity=4)
        total = self.cart.total(coupon="SAVE5")
        assert total == pytest.approx(249.99)
