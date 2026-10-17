import pytest
import cart

# --- Helper functions -----------------------------------------------------

def round2(x):
    return round(float(x), 2)

# --- Tests for apply_discount ---------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),            # example from spec
        (100, 0, 100.0),             # no discount
        (50, 100, 0.0),              # full discount
        (99.99, 33, round2(66.66)), # arbitrary values
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Invalid inputs for apply_discount ----------------------------------------
@pytest.mark.parametrize(
    "price, percent",
    [
        (-1, 10),          # negative price
        (100, -5),         # negative percent
        (100, 105),        # percent > 100
        (-10, -20),       # both invalid
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- Tests for bulk_discount_percent -------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (250, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid inputs for bulk_discount_percent ---------------------------------
@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2, "10"],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- Tests for parse_coupon ----------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe50", 50),
        ("saVE1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",      # out of range N
        "SAVE51",     # out of range
        "DISCOUNT5",  # wrong prefix
        "savelow",    # not numeric
        "",           # empty
        None,          # non‑string
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- Tests for shipping_fee ---------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),      # below threshold, non‑member
        (999.99, True, 30),   # just below free, member gets half
        (1000, False, 0),     # exactly threshold
        (1500, True, 0),      # above threshold, still free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# Invalid subtotal --------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal",
    [-10, -0.01],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Tests for Cart class -----------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_add_item_simple(self):
        self.cart.add_item("apple", unit_price=50, quantity=2)
        assert self.cart.items() == {"apple": (50, 2)}
        assert self.cart.subtotal() == 100.0

    def test_add_multiple_items(self):
        self.cart.add_item("banana", unit_price=30, quantity=3)
        self.cart.add_item("orange", unit_price=20, quantity=5)
        expected = {"banana": (30, 3), "orange": (20, 5)}
        assert self.cart.items() == expected
        assert self.cart.subtotal() == 30 * 3 + 20 * 5

    def test_add_same_item_increases_quantity(self):
        self.cart.add_item("pear", unit_price=15)
        self.cart.add_item("pear", unit_price=15, quantity=4)
        assert self.cart.items() == {"pear": (15, 5)}

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("mango", unit_price=25, quantity=3)
        self.cart.remove_item("mango", quantity=1)
        assert self.cart.items() == {"mango": (25, 2)}
        # remove remaining
        self.cart.remove_item("mango")
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", quantity=1)

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("widget", unit_price=200, quantity=5)  # subtotal 1000
        assert self.cart.total() == 1000.0

    def test_total_with_member_discount_and_coupons(self):
        # Add 120 units of a single item to trigger bulk discount
        self.cart.add_item("gadget", unit_price=10, quantity=120)  # subtotal 1200
        # member gets half shipping fee (free because subtotal >=1000)
        # Apply coupon SAVE20 => 20% off on the discounted subtotal
        result = self.cart.total(member=True, coupon="SAVE20")
        # Expected steps:
        # 1. bulk discount: 15% of 1200 => 180 -> discounted_subtotal=1020
        # 2. coupon: 20% of 1020 => 204 -> subtotal_after_coupon=816
        # 3. shipping fee: 0 (subtotal >=1000)
        expected = 816.0
        assert result == expected

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("thing", unit_price=50, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
