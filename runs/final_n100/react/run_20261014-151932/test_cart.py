import cart
import pytest

# Helper to assert rounding

def assert_close(a, b, eps=1e-9):
    assert abs(a - b) < eps

# Test apply_discount with valid values
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),     # no discount
        (50, 100, 0.0),      # full free
        (123.456, 10, 111.11)  # rounding check
    ]
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Test apply_discount errors
@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-10, 110]
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Shipping fee tests
@pytest.mark.parametrize(
    "subtotal, expected",
    [
        (0, 60.0),
        (500, 60.0),
        (999.99, 60.0),
        (1000, 0.0),
        (1500, 0.0)
    ]
)
def test_shipping_fee_regular(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (200, True, 30.0),
        (1200, True, 0.0),
        (50, False, 60.0)
    ]
)
def test_shipping_fee_member(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# Shipping fee error on negative subtotal
def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# Coupon parsing tests
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SaVe30   ", 30),
        ("SaVe1", 1),
        ("SaVe50", 50)
    ]
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code",
    ["SAVE0", "SAVE51", "DISCOUNT10", "", "SAVEXX", "save-5", "  "]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Cart tests: basic functionality
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 2.5, 3)
        self.cart.add_item("banana", 1.0)
        items = self.cart.items()
        assert len(items) == 2
        # Each item is a dict or tuple? Assume list of tuples (name, price, qty)
        names = [item[0] for item in items]
        assert set(names) == {"apple", "banana"}

    def test_subtotal(self):
        self.cart.add_item("a", 10.0, 2)  # total 20
        self.cart.add_item("b", 5.0, 1)
        assert self.cart.subtotal() == 25.0

    def test_total_no_coupon(self):
        self.cart.add_item("item", 200, 1)
        # subtotal 200 < 1000 => shipping 60
        assert self.cart.total(member=False) == 260.0
        # member gets half shipping: 30
        assert self.cart.total(member=True) == 230.0

    def test_total_with_coupon(self):
        self.cart.add_item("item", 100, 5)  # subtotal 500
        # apply 10% coupon: discounted subtotal = 450 -> shipping 60 => total 510
        assert self.cart.total(coupon="SAVE10") == 510.0
        # member: discounted subtotal 450 < 1000 => shipping 30 => total 480
        assert self.cart.total(member=True, coupon="SAVE10") == 480.0

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

# Remove item tests
    def test_remove_item_quantity(self):
        self.cart.add_item("x", 5, 3)
        self.cart.remove_item("x", 2)
        items = self.cart.items()
        assert items[0][2] == 1  # remaining qty

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")
