import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),           # example from spec
        (100, 0, 100.0),            # no discount
        (50, 100, 0.0),             # full price removed
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid values
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (20, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, (int, float)) else cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save5 ", 5),   # case-insensitive and spaces ignored
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVExx", "SAVE0", "SAVEDOZEN", "SAVE-5", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart and total calculation ----------
class TestCartTotal:
    def setup_method(self):
        self.cart = cart.Cart()

    def add_items(self, items):
        for name, price, qty in items:
            self.cart.add_item(name, price, qty)

    def test_empty_total(self):
        assert self.cart.total() == 0.00

    def test_simple_subtotal_no_coupon_or_shipping(self):
        self.add_items([("apple", 10.0, 2), ("banana", 5.0, 1)])
        # subtotal = 25
        assert self.cart.subtotal() == 25.00
        assert self.cart.total(member=False) == 85.0  # 25 + shipping 60

    def test_coupon_and_shipping(self):
        self.add_items([("widget", 200.0, 1)])
        # subtotal = 200
        total_no_coupon = 260.0  # 200 + 60
        assert self.cart.total(member=False) == total_no_coupon
        # coupon SAVE10 -> 10% off => 180; shipping on 180 => 60
        assert self.cart.total(coupon="SAVE10") == 240.0

    def test_member_discount_and_shipping(self):
        self.add_items([("gadget", 120.0, 1)])
        # subtotal = 120, coupon none, member pays half shipping -> 30
        assert self.cart.total(member=True) == 150.0

    def test_coupon_invalid_raises(self):
        self.add_items([("item", 50.0, 1)])
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_bulk_discount_applied_in_subtotal(self):
        # buying 60 units gives bulk discount of 10%
        self.add_items([("bulk_item", 5.0, 60)])
        # subtotal before discounts = 300
        # bulk discount: 10% -> 270
        assert self.cart.subtotal() == 270.00
        # no coupon or shipping for simplicity
        assert self.cart.total(member=False) == 330.0  # 270 + 60 shipping

    def test_rounding(self):
        self.add_items([("odd", 33.333, 3)])  # subtotal = 99.999
        # bulk discount none, coupon SAVE1 => 1% off -> 98.98999...
        total = self.cart.total(coupon="SAVE1")
        assert isinstance(total, float)
        assert round(total, 2) == 158.99  # 99.999*0.99 + 60

# Ensure that Cart.items returns a list of dicts with keys name, unit_price, quantity.
def test_cart_items_structure():
    c = cart.Cart()
    c.add_item("pen", 1.5, 4)
    items = c.items()
    assert isinstance(items, list)
    assert len(items) == 1
    d = items[0]
    for key in ("name", "unit_price", "quantity"):
        assert key in d
    assert d["name"] == "pen"
    assert d["unit_price"] == 1.5
    assert d["quantity"] == 4
