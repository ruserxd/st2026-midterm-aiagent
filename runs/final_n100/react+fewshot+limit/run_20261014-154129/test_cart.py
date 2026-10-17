import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.00),
    (100, 100, 0.00),
])
def test_apply_discount_edges(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-10, 20),          # negative price
    (50, -5),           # percent < 0
    (50, 105),          # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.7])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe50  ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "DISCOUNT10",
    "savelink",
    "  ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal, member, expected", [
    (999.99, False, 60),
    (1000, True, 0),
    (1200, False, 0),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new(self):
        self.c.add_item("apple", 1.5, 3)
        assert self.c.items() == {"apple": 3}

    def test_add_item_increase_same_price(self):
        self.c.add_item("banana", 0.75, 2)
        self.c.add_item("banana", 0.75, 1)
        assert self.c.items() == {"banana": 3}

    def test_add_item_different_price_error(self):
        self.c.add_item("orange", 0.9, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.0, 1)

    def test_add_item_invalid_arguments(self):
        with pytest.raises(ValueError):
            self.c.add_item("pear", -1, 2)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1, 0)

    def test_remove_item_partial(self):
        self.c.add_item("mango", 2.0, 5)
        self.c.remove_item("mango", 3)
        assert self.c.items() == {"mango": 2}

    def test_remove_item_zero_removes(self):
        self.c.add_item("melon", 1.0, 2)
        self.c.remove_item("melon", 2)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonitem", 1)

    def test_subtotal_with_bulk_discount(self):
        # 5 apples at $10 each -> bulk discount 0%
        self.c.add_item("apple", 10.0, 5)
        # 15 bananas at $2 each -> bulk discount 5%
        self.c.add_item("banana", 2.0, 15)
        # subtotal: apple 50, banana before discount 30
        # banana discount 5% => 30 * 0.95 = 28.5
        # total expected 78.5
        assert self.c.subtotal() == 78.50

    def test_total_no_coupon_member(self):
        self.c.add_item("widget", 200.0, 6)  # 10% bulk discount: 200*6=1200 -> *0.9=1080
        total = self.c.total(member=True)
        # subtotal after coupon none => 1080; shipping fee member: subtotal<1000? actually 1080>=1000 free
        assert total == 1080.00

    def test_total_with_coupon_and_shipping(self):
        self.c.add_item("gadget", 150.0, 4)  # no bulk discount => 600
        total = self.c.total(coupon="SAVE20")
        # subtotal 600 -> coupon 20% => 480
        # shipping: subtotal<1000 so fee 60
        # final total 540
        assert total == 540.00

    def test_total_empty_cart(self):
        assert self.c.total() == 0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="INVALID")
