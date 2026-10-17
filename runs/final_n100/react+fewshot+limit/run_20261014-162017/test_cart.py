import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),            # no discount
    (150, 100, 0.0),           # full discount
    (123.45, 12.5, round(123.45 * 0.875, 2)),
])
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-1, 10),            # negative price
    (50, -5),            # negative percent
    (30, 105),           # percent >100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------------------
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),          # below 10
    (10, 5),         # boundary at 10
    (49, 5),         # just before 50
    (50, 10),        # boundary at 50
    (99, 10),        # just before 100
    (100, 15),       # boundary at 100
    (150, 15),       # above 100
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",      # N <1
    "SAVE51",     # N >50
    "SAVEBAR",    # non-digit
    "HELLO10",    # wrong prefix
    "",           # empty
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (999.99, False, 60),   # below free threshold
    (1000, False, 0),      # exactly threshold
    (1500, True, 30),     # member gets half
    (800, True, 30),       # member half
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class -----------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    # adding items
    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 2}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.8, 3)
        self.cart.add_item("banana", 0.8, 2)
        assert self.cart.items() == {"banana": 5}

    def test_add_item_invalid_unit_price(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -1.0, 1)

    def test_add_item_invalid_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 2.0, 0)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("mango", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("mango", 3.5, 1)

    # removing items
    def test_remove_partial(self):
        self.cart.add_item("grape", 2.0, 4)
        self.cart.remove_item("grape", 2)
        assert self.cart.items() == {"grape": 2}

    def test_remove_entire(self):
        self.cart.add_item("melon", 5.0, 3)
        self.cart.remove_item("melon", 3)
        assert self.cart.items() == {}

    def test_remove_more_than_exists(self):
        self.cart.add_item("berry", 1.0, 2)
        self.cart.remove_item("berry", 5)   # should remove item entirely
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("kiwi", 1)

    # subtotal calculation
    def test_subtotal_with_bulk_discount(self):
        # 12 items, bulk discount 5%
        self.cart.add_item("widget", 10.0, 12)
        expected = round(10.0 * 12 * 0.95, 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_empty(self):
        assert self.cart.subtotal() == 0

    # total calculation
    def test_total_no_coupon_non_member(self):
        self.cart.add_item("item", 200.0, 1)
        # subtotal =200, no coupon, shipping fee=60 (subtotal<1000)
        expected = round(200 + 60, 2)
        assert self.cart.total() == expected

    def test_total_coupon_non_member(self):
        self.cart.add_item("item", 200.0, 1)
        # coupon SAVE10 -> 10%
        subtotal_after_coupon = apply_discount(200, 10)  # 180
        shipping = shipping_fee(subtotal_after_coupon, member=False)  # 60
        expected = round(subtotal_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected

    def test_total_member_shipping_half(self):
        self.cart.add_item("item", 200.0, 1)
        subtotal = 200
        shipping = shipping_fee(subtotal, member=True)  # 30
        expected = round(subtotal + shipping, 2)
        assert self.cart.total(member=True) == expected

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
