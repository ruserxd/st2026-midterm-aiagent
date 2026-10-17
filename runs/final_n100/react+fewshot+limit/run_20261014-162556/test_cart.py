import pytest
import cart

# ---------- Utility helpers for expected values from spec ----------

def _expected_bulk_discount(quantity):
    if quantity >= 100:
        return 15
    if quantity >= 50:
        return 10
    if quantity >= 10:
        return 5
    return 0

# --------------------- apply_discount ---------------------------------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.00),      # example from spec
    (100, 0, 100.00),       # no discount
    (50, 100, 0.00),        # full discount
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 20),            # negative price
    (100, -5),             # percent too low
    (100, 120),            # percent too high
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --------------------- bulk_discount_percent -------------------------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),      # below 10
    (10, 5),     # exactly 10
    (49, 5),     # just below 50
    (50, 10),    # exactly 50
    (99, 10),    # just below 100
    (100, 15),   # exactly 100
    (150, 15),   # above 100
])
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "ten"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------------------- parse_coupon ---------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEXX",     # no number
    "SAVE0",      # out of range
    "SAVE51",     # out of range
    "DISCOUNT10",# wrong prefix
    "",           # empty string
    123,          # non‑string
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------------------- shipping_fee ---------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),      # not free, non‑member
    (1200, True, 0),       # free for any member flag
    (1000, False, 0),      # exactly threshold
    (999.99, False, 60),   # just below threshold
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------------------- Cart class -----------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 2.5, 2)
        self.cart.add_item("banana", 2.5, 1)
        assert self.cart.items() == {"banana": 3}

    def test_add_item_invalid_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, 0)

    def test_add_item_different_price(self):
        self.cart.add_item("mango", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("mango", 4.0, 2)

    def test_remove_item_existing(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        # remove the rest
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_item_not_present(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_with_bulk_discount(self):
        # 12 apples at $1 each -> bulk discount 5%
        self.cart.add_item("apple", 1.0, 12)
        # 60 bananas at $2 each -> bulk discount 10%
        self.cart.add_item("banana", 2.0, 60)
        expected = round(12*1*(100-5)/100 + 60*2*(100-10)/100, 2)
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_member(self):
        self.cart.add_item("item", 200.0, 1)
        # subtotal = 200, coupon none, shipping fee 60 (non‑member), total = 260
        assert self.cart.total(member=False) == 260.00

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 500.0, 1)
        # subtotal = 500, coupon SAVE10 -> 450, shipping fee 60 (non‑member), total 510
        assert self.cart.total(member=False, coupon="SAVE10") == 510.00

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("item", 100.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.00
