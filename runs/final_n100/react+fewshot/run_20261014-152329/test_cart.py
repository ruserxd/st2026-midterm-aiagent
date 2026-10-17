import pytest
import cart

# --- apply_discount -------------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent -------------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),      # below 10
        (10, 5),     # at threshold
        (49, 5),     # just below 50
        (50, 10),    # at threshold
        (99, 10),    # just below 100
        (100, 15),   # at threshold
        (150, 15),   # above
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ----------------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE30 ", 30),
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",          # N < 1
    "SAVE51",         # N > 50
    "DISCOUNT10",     # wrong prefix
    "SAVE-5",         # negative
    "SAVEXY",        # non-integer
    "",               # empty string
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ----------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (500, False, 60),   # non-member below threshold
        (1000, False, 0),   # exactly threshold
        (1500, True, 0),    # above threshold even as member
        (800, True, 30),    # member below threshold
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class -------------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_and_subtotal(self):
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.subtotal() == 4.5

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 0.8, 2)
        self.cart.add_item("banana", 0.8, 4)
        # subtotal should reflect total quantity
        assert self.cart.subtotal() == 6 * 0.8

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("orange", 1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.2, 1)

    def test_remove_partial(self):
        self.cart.add_item("carrot", 0.5, 4)
        self.cart.remove_item("carrot", 2)
        assert self.cart.subtotal() == 2 * 0.5

    def test_remove_complete_and_exception(self):
        self.cart.add_item("lettuce", 1.0, 3)
        self.cart.remove_item("lettuce", 3)
        # item should no longer be in cart; subtotal zero
        assert self.cart.subtotal() == 0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mushroom")

    def test_total_returns_float_and_is_consistent_with_subtotal(self):
        # Add items and verify that total is at least subtotal (shipping may add)
        self.cart.add_item("bread", 2.0, 1)
        self.cart.add_item("milk", 1.5, 1)
        base = self.cart.subtotal()
        t = self.cart.total()
        assert isinstance(t, float)
        assert t >= base
        # member discount on shipping should reduce total compared to non-member
        t_member = self.cart.total(member=True)
        t_nonmember = self.cart.total(member=False)
        assert t_member <= t_nonmember
