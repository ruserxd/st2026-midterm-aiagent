import pytest
import cart

# Helper to check rounding for floats

def approx_equal(a, b):
    return abs(a - b) < 1e-9

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price",
    [-1, -0.01],
)
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 105],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
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
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 2.5],
)
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "DISCOUNT10", "", "  ", "SAVE-5", "SAVExx"] ,
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (0, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -10],
)
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # items and add_item/remove_item interaction
    def test_add_and_items(self):
        assert self.cart.items() == {}
        self.cart.add_item("apple", 1.0, quantity=3)
        self.cart.add_item("banana", 0.5, quantity=2)
        assert self.cart.items() == {"apple": 3, "banana": 2}

    def test_add_same_name_increases_quantity(self):
        self.cart.add_item("orange", 0.8, quantity=1)
        self.cart.add_item("orange", 0.8, quantity=4)
        assert self.cart.items() == {"orange": 5}

    def test_add_same_name_different_price_raises(self):
        self.cart.add_item("pear", 2.0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 3.0)

    def test_remove_item_decrements_quantity(self):
        self.cart.add_item("milk", 1.5, quantity=5)
        self.cart.remove_item("milk", quantity=2)
        assert self.cart.items() == {"milk": 3}

    def test_remove_item_removes_when_zero_or_less(self):
        self.cart.add_item("eggs", 0.1, quantity=4)
        self.cart.remove_item("eggs", quantity=4)  # exactly zero
        assert "eggs" not in self.cart.items()
        self.cart.add_item("bread", 2.0, quantity=3)
        self.cart.remove_item("bread", quantity=5)  # more than existing
        assert "bread" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_calculation(self):
        self.cart.add_item("pen", 0.5, quantity=10)
        self.cart.add_item("notebook", 2.0, quantity=3)
        assert self.cart.subtotal() == 0.5 * 10 + 2.0 * 3

    def test_total_without_member_or_coupon(self):
        # items: pen 5.0, notebook 6.0 -> subtotal 11.0
        self.cart.add_item("pen", 0.5, quantity=10)
        self.cart.add_item("notebook", 2.0, quantity=3)
        total = self.cart.total()
        # shipping fee for 11 < 1000 is 60
        assert total == 11.0 + 60

    def test_total_with_member(self):
        self.cart.add_item("item", 200.0, quantity=6)  # subtotal 1200
        # free shipping because >= 1000
        assert self.cart.total(member=True) == 1200.0

    def test_total_with_coupon_and_bulk_discount(self):
        # buy 20 units of a product -> bulk discount percent 5%
        self.cart.add_item("widget", 10.0, quantity=20)
        # subtotal before discounts: 200
        # apply bulk discount: 200 * (1-0.05) = 190
        # apply coupon SAVE10 => 190 * (1-0.10) = 171
        # shipping fee for 171 < 1000 is 60
        assert self.cart.total(coupon="SAVE10") == 171 + 60

    def test_total_with_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
