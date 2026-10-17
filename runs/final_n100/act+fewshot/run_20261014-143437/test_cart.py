import pytest
import cart

# ---------- apply_discount -------------------------------------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundaries: negative price or percent out of range
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent --------------------------------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    ("  SaVe20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVEX10",
    "SAVEE15",
    "HELLO",
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new_and_existing(self):
        self.c.add_item("apple", 1.00, 5)
        # bulk discount: 5 -> no discount
        assert self.c.items() == {"apple": 5}
        assert self.c.subtotal() == 5.0

        self.c.add_item("apple", 1.00, 10)
        # now quantity 15 => bulk 5% discount on all apples
        expected_sub = round(1.00 * 15 * 0.95, 2)
        assert self.c.items() == {"apple": 15}
        assert self.c.subtotal() == expected_sub

    def test_add_item_price_mismatch(self):
        self.c.add_item("banana", 0.50)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 0.60)

    def test_remove_item_partial_and_full(self):
        self.c.add_item("orange", 2.00, 3)
        self.c.remove_item("orange", 1)
        assert self.c.items() == {"orange": 2}
        self.c.remove_item("orange", 2)
        assert "orange" not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("pear")

    def test_total_with_coupon_and_member(self):
        # add items to trigger bulk discount
        self.c.add_item("widget", 100.0, 10)   # 5% off -> 950.0
        subtotal = 950.0
        coupon = "SAVE20"
        after_coupon = round(subtotal * (1 - 0.20), 2)
        shipping = cart.shipping_fee(after_coupon, member=True)  # half of 60 =>30 unless free
        total_expected = round(after_coupon + shipping, 2)
        assert self.c.total(member=True, coupon=coupon) == total_expected

    def test_total_no_shipping_when_free(self):
        self.c.add_item("mega", 200.0, 10)  # subtotal 1900 after 5% off
        assert self.c.total() == cart.shipping_fee(1900, member=False) + round(1900 * (1 - 0), 2)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")
