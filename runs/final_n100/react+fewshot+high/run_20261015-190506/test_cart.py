import pytest
import cart

# --- apply_discount ---------------------------------------------------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [
        (-1, 10),      # price must be >= 0
        (100, -5),     # percent < 0
        (100, 105),    # percent > 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent --------------------------------------------

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),     # <10
        (10, 5),    # >=10
        (49, 5),    # <50 but >=10
        (50, 10),   # >=50
        (99, 10),   # <100 but >=50
        (100, 15),  # >=100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 1.5],  # non‑positive or non‑int
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -----------------------------------------------------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),      # case‑insensitive
        (" SAVE30 ", 30),     # surrounding whitespace ignored
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVEX",          # missing number
        "SAVE0",          # N<1
        "SAVE51",         # N>50
        "10SAVE",         # wrong order
        "",               # empty string
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -----------------------------------------------------

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),      # below 1000, non‑member
        (0, True, 30),       # below 1000, member pays half
        (999.99, True, 30),   # just below threshold
        (1000, False, 0),     # free shipping
        (1500, True, 0),      # free shipping even for members
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],  # negative subtotal not allowed
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class -------------------------------------------------------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # add_item and items ----------------------------------------------

    def test_add_new_item_and_items_dict(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_existing_item_increases_quantity(self):
        self.cart.add_item("banana", 2.5, 2)
        self.cart.add_item("banana", 2.5, 1)
        assert self.cart.items() == {"banana": 3}

    def test_add_item_invalid_price_or_qty(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1.0, 1)   # negative price
        with pytest.raises(ValueError):
            self.cart.add_item("peach", 1.5, 0)   # zero quantity
        with pytest.raises(ValueError):
            self.cart.add_item("plum", 2.0, -3)   # negative quantity

    def test_add_item_different_price_raises(self):
        self.cart.add_item("melon", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("melon", 4.0, 2)

    # remove_item -------------------------------------------------------

    def test_remove_partial_and_full_quantity(self):
        self.cart.add_item("plum", 1.5, 4)
        self.cart.remove_item("plum", 2)
        assert self.cart.items() == {"plum": 2}
        # remove remaining quantity – should disappear from dict
        self.cart.remove_item("plum", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("non-existent", 1)

    # subtotal ----------------------------------------------------------

    def test_subtotal_with_bulk_discount_and_rounding(self):
        self.cart.add_item("apple", 1.0, 3)   # no discount
        self.cart.add_item("orange", 2.0, 12) # 5% discount
        assert self.cart.subtotal() == 25.8

    def test_subtotal_empty_cart(self):
        assert self.cart.subtotal() == 0

    # total -------------------------------------------------------------

    def test_total_with_coupon_and_shipping_member(self):
        self.cart.add_item("widget", 50.0, 2)   # subtotal 100
        total = self.cart.total(member=True, coupon="SAVE10")
        assert total == 120.0

    def test_total_no_coupon_non_member(self):
        self.cart.add_item("gadget", 200.0, 1)
        assert self.cart.total() == 260.0

    def test_total_shipping_fee_after_discount(self):
        # subtotal before coupon is 1200 (>=1000) but after 10% discount
        # it becomes 1080 which still meets the >=1000 threshold for free shipping.
        self.cart.add_item("expensive", 200.0, 6)   # 6 * 200 = 1200
        total = self.cart.total(coupon="SAVE10")
        assert total == 1080.0

    def test_total_coupon_invalid_raises(self):
        self.cart.add_item("tool", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_zero_cost(self):
        assert self.cart.total() == 0
