import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 25, 92.09), # 123.45*0.75=92.5875 -> 92.59? round to 2 decimals
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid price or percent
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
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

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SaVe20 ", 20),
        ("sAvE1", 1),
        ("SAVE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVe-10", "1234", " "])  # invalid cases
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart.total and related behaviour ----------
class TestCartTotal:
    def setup_method(self):
        self.cart = cart.Cart()

    def add_item(self, name="item", unit_price=100.0, quantity=1):
        self.cart.add_item(name, unit_price, quantity)

    def test_empty_cart_total(self):
        assert self.cart.total() == 0.0

    def test_subtotal_and_add_items(self):
        self.add_item("a", 50, 2)   # 100
        self.add_item("b", 30, 1)   # 130
        assert self.cart.subtotal() == 130.0
        # no coupon, not member -> subtotal + shipping(60) = 190
        assert self.cart.total() == 190.0

    def test_coupon_reduction(self):
        self.add_item("x", 200, 1)
        # subtotal 200; apply SAVE10 => 180, shipping 60 => 240
        assert self.cart.total(coupon="SAVE10") == 240.0

    def test_invalid_coupon_raises(self):
        self.add_item("y", 50, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_member_discount_and_shipping_half(self):
        self.add_item("z", 1200, 1)   # subtotal 1200 free shipping
        assert self.cart.total(member=True) == 1200.0
        # if not member but still >1000: free
        assert self.cart.total(member=False) == 1200.0

    def test_shipping_fee_with_coupon(self):
        # subtotal 900, coupon SAVE20 => 720, shipping 60 => 780
        self.add_item("c", 300, 3)
        assert self.cart.total(coupon="SAVE20") == 780.0

    def test_bulk_discount_percent_applied_per_item(self):
        # Adding 12 units of 'bulk' should give 5% per unit on that line
        self.add_item("bulk", 100, 12)
        # line total before coupon: 1200 * 0.95 = 1140
        assert self.cart.total() == pytest.approx(1140 + 60)  # shipping 60

    def test_bulk_discount_and_member(self):
        # 150 units, member free shipping
        self.add_item("bulk", 10, 150)
        line_total = 150 * 10 * 0.85  # 15% discount
        assert self.cart.total(member=True) == pytest.approx(line_total)
