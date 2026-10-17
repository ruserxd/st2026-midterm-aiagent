import pytest
import cart

# --- Utility helper to assert rounded value

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount tests ---------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),      # example from spec
    (100, 0, 100.0),       # no discount
    (50, 100, 0.0),        # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent tests -------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),   # below 10
    (10, 5),  # boundary
    (49, 5),  # just below 50
    (50, 10), # boundary
    (99, 10), # just below 100
    (100, 15),# boundary
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 2.5])
def test_bulk_discount_invalid_quantity_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ---------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30  ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",      # below range
    "SAVE51",     # above range
    "INVALID",    # wrong pattern
    "",           # empty
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ---------
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),   # just below free threshold
    (1000, False, 0),      # exact threshold
    (1500, True, 30),      # member pays half
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ---------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # Adding items -----------------------------------------------------
    def test_add_item_new(self):
        self.cart.add_item("apple", unit_price=2, quantity=3)
        assert self.cart.items() == {"apple": 3}
        # Subtotal: 2*3 = 6 (no bulk discount yet)
        assert round2(self.cart.subtotal()) == 6.0

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1, 2)
        self.cart.add_item("banana", 1, 3)  # same price
        assert self.cart.items() == {"banana": 5}
        # Subtotal: 1*5 = 5 (no bulk discount yet)
        assert round2(self.cart.subtotal()) == 5.0

    def test_add_item_existing_different_price_raises(self):
        self.cart.add_item("orange", 3, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4, 1)  # price mismatch

    def test_add_invalid_unit_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1, 0)   # quantity not positive

    # Removing items -----------------------------------------------------
    def test_remove_partial(self):
        self.cart.add_item("mango", 5, 4)
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {"mango": 2}

    def test_remove_exact_quantity_removes_item(self):
        self.cart.add_item("peach", 7, 3)
        self.cart.remove_item("peach", 3)
        assert self.cart.items() == {}

    def test_remove_more_than_available_removes_item_and_no_error(self):
        self.cart.add_item("plum", 4, 2)
        # removing more than exists should simply remove the item
        self.cart.remove_item("plum", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    # Subtotal calculation with bulk discount ----------------------------
    def test_subtotal_with_bulk_discount(self):
        # Buy 10 units, expect 5% discount on that item
        self.cart.add_item("widget", 20, 10)   # unit price 20
        expected = round2(20 * 10 * (1 - 0.05))
        assert round2(self.cart.subtotal()) == expected

    def test_subtotal_multiple_items_bulk_discount_individual(self):
        self.cart.add_item("widget", 30, 5)   # no bulk discount
        self.cart.add_item("gadget", 10, 15)  # 5% discount
        subtotal_widget = round2(30 * 5)
        subtotal_gadget = round2(10 * 15 * (1 - 0.05))
        assert round2(self.cart.subtotal()) == round2(subtotal_widget + subtotal_gadget)

    # Total calculation ---------------------------------------------------
    def test_total_no_coupon_member_false(self):
        self.cart.add_item("item", 100, 5)  # no bulk discount
        # Subtotal = 500, shipping 60 (not member), total = 560
        assert round2(self.cart.total(member=False)) == 560.0

    def test_total_coupon_applied(self):
        self.cart.add_item("item", 200, 5)
        # subtotal = 1000 -> free shipping
        # coupon SAVE10 => 10% off: 900
        assert round2(self.cart.total(coupon="SAVE10")) == 900.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 50, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_member_shows_half_shipping(self):
        self.cart.add_item("big", 800, 2)  # subtotal 1600 > free threshold
        # shipping 0, total = 1600
        assert round2(self.cart.total(member=True)) == 1600.0

    def test_total_empty_cart_costs_zero_no_shipping(self):
        # Empty cart: total should be 0 and no shipping
        assert round2(self.cart.total()) == 0.0
