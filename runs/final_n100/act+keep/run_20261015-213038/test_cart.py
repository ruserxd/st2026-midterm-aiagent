import pytest
import cart

# --------- apply_discount ----------------------------------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),        # example from spec
    (100, 0, 100.0),         # no discount
    (100, 100, 0.0),         # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# price must be non-negative
@pytest.mark.parametrize("price", [-1, -10.5])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

# percent bounds
@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# rounding to two decimals
assert cart.apply_discount(1.235, 10) == 1.11

# --------- bulk_discount_percent ----------------------------------------

@pytest.mark.parametrize("quantity,expected", [
    (99, 0),   # below 100
    (100, 15), # threshold inclusive
    (50, 10),  # threshold inclusive
    (10, 5),   # threshold inclusive
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------- parse_coupon -----------------------------------------------
valid_codes = {
    "SAVE10": 10,
    "save10": 10,          # case-insensitive
    " SAVE5 ": 5,           # whitespace ignored
}

@pytest.mark.parametrize("code,expected", valid_codes.items())
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAV10", "SAVE0", "SAVE51", "123", ""]
for code in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------- shipping_fee -----------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),   # free at threshold
    (999.99, False, 60),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------- Cart.total -----------------------------------------------
class TestCartTotal:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_no_shipping(self):
        assert self.cart.total() == 0

    def test_subtotal_without_coupon_or_shipping(self):
        self.cart.add_item("widget", unit_price=100, quantity=2)
        # subtotal = 200
        assert self.cart.subtotal() == 200
        # total without coupon - shipping fee applied (subtotal < 1000) = +60
        assert self.cart.total() == 260

    def test_coupon_applied_before_shipping(self):
        self.cart.add_item("gadget", unit_price=50, quantity=3)
        # subtotal = 150
        # coupon SAVE10 - 10% off: 135
        # shipping on 135 = 60
        assert self.cart.total(coupon="SAVE10") == 195

    def test_shipping_free_with_large_subtotal(self):
        self.cart.add_item("expensive", unit_price=500, quantity=3)
        # subtotal = 1500
        # no coupon - total = 1500 (shipping free)
        assert self.cart.total() == 1500

    def test_invalid_coupon_raises(self):
        self.cart.add_item("item", 10, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_member_shipping_half_fee(self):
        self.cart.add_item("thing", unit_price=20, quantity=5)  # subtotal 100
        # no coupon: shipping 60 - member pays 30
        assert self.cart.total(member=True) == 130

    def test_rounding_to_two_decimals(self):
        self.cart.add_item("precise", unit_price=1.235, quantity=10)  # subtotal 12.35
        # no coupon: shipping 60 - total 72.35 rounded to 2 dec = 72.35
        assert self.cart.total() == 72.35
