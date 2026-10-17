import pytest
import cart

# Helper function to compare floats with spec rounding

def round2(x):
    return round(float(x), 2)

# ---- apply_discount -------------------------------------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full discount
])
def test_apply_discount(price, percent, result):
    assert round2(cart.apply_discount(price, percent)) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ------------------------------------------

@pytest.mark.parametrize("qty,expected", [
    (1, 0),
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

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon -----------------------------------------------------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",          # below min
    "SAVE51",         # above max
    "DISCOUNT10",
    "save",           # missing number
    "" ,              # empty
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -----------------------------------------------------

@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart functionality ----------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_totals_zero(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_and_remove_item(self):
        self.cart.add_item("apple", unit_price=2.5, quantity=3)
        # subtotal should be 7.5
        assert round2(self.cart.subtotal()) == 7.5
        # remove one apple
        self.cart.remove_item("apple", quantity=1)
        assert round2(self.cart.subtotal()) == 5.0
        # remove remaining two apples
        self.cart.remove_item("apple")
        assert round2(self.cart.subtotal()) == 0

    def test_bulk_discount_applied_in_total(self):
        # buying 120 of the same item gives 15% bulk discount
        self.cart.add_item("widget", unit_price=10.0, quantity=120)
        # subtotal is 1200; coupon not used
        assert round2(self.cart.subtotal()) == 1200
        # total should be subtotal (no shipping, free over 1000) minus bulk discount
        # bulk_discount_percent gives 15% -> apply_discount(1200,15)=1020
        assert round2(self.cart.total()) == 1020.0

    def test_coupon_and_shipping_in_total(self):
        self.cart.add_item("gadget", unit_price=100, quantity=5)  # subtotal 500
        # no bulk discount
        # apply coupon SAVE10 (10%) -> 450
        # shipping for non-member on 450 is 60
        assert round2(self.cart.total(coupon="SAVE10")) == 510.0

    def test_member_shipping_and_coupon(self):
        self.cart.add_item("thing", unit_price=200, quantity=4)  # subtotal 800
        # coupon SAVE5 -> 760
        # member shipping half of 60 =30 (since subtotal<1000)
        assert round2(self.cart.total(member=True, coupon="SAVE5")) == 790.0

    def test_invalid_coupon_raises_in_total(self):
        self.cart.add_item("item", unit_price=10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
