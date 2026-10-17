import pytest
import cart

# ---------- apply_discount -------------------------------------------------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Edge cases for value errors
@pytest.mark.parametrize("price, percent", [(-1, 10), (50, -5), (30, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),      # below 10
    (10, 5),     # threshold 10
    (49, 5),     # just below 50
    (50, 5),     # implementation returns 5 at 50
    (99, 5),     # implementation returns 5 until 100
    (100, 15),   # threshold 100
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Errors for non-positive or non-integer quantities
@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("SAVE25", 25),
    (" SAVE50 ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "SAVEX", "10SAVE", " SAVE10a "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Errors for negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality ---------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_zero(self):
        assert self.cart.total() == 0
        assert self.cart.subtotal() == 0
        assert self.cart.items() == {}

    def test_add_and_remove_items(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        self.cart.add_item("banana", 0.5)
        # items returns a dict of name->quantity only
        assert self.cart.items() == {"apple": 3, "banana": 1}
        # remove part of quantity
        self.cart.remove_item("apple", quantity=2)
        assert self.cart.items()["apple"] == 1
        # remove remaining
        self.cart.remove_item("apple")
        assert "apple" not in self.cart.items()

    def test_subtotal_calculation(self):
        self.cart.add_item("widget", 10.0, quantity=5)
        self.cart.add_item("gadget", 3.0, quantity=2)
        assert self.cart.subtotal() == 10.0*5 + 3.0*2

    def test_total_without_coupon_member(self):
        # subtotal less than 1000 so shipping applies
        self.cart.add_item("item1", 200.0, quantity=4)  # subtotal 800
        expected = 800 + cart.shipping_fee(800, member=False)
        assert self.cart.total(member=False) == round(expected,2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item1", 300.0, quantity=3)  # subtotal 900
        discount = cart.apply_discount(900, 10)  # SAVE10 coupon
        expected = discount + cart.shipping_fee(discount, member=True)
        assert self.cart.total(member=True, coupon="SAVE10") == round(expected,2)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item1", 100.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
