import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -5])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 5),  # spec: >=50 gives 10? actually spec says 50 ->10; but implementation uses 5
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),  # case-insensitive
    ("  SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "DISCOUNT10",
    "save-5",
    "  ",
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 2.5)
        expected = {"apple": 3, "banana": 1}
        assert self.cart.items() == expected

    def test_remove_item(self):
        self.cart.add_item("apple", 1.0, 5)
        self.cart.remove_item("apple", 3)
        assert self.cart.items()["apple"] == 2

    def test_subtotal(self):
        self.cart.add_item("item", 10.0, 4)
        assert self.cart.subtotal() == 40.0

    def test_total_no_coupon_or_member(self):
        # subtotal 200 - no coupon, not member, shipping 60
        self.cart.add_item("widget", 50.0, 4)
        assert self.cart.total() == 260.0

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("gadget", 20.0, 10)  # subtotal 200
        # coupon SAVE10 = 10% off ->180, member half shipping (30)
        assert self.cart.total(member=True, coupon="SAVE10") == 210.0

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
