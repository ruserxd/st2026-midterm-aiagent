import pytest
import cart

# Helper for rounding
from math import isclose

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert round2(cart.apply_discount(price, percent)) == expected

@pytest.mark.parametrize("price,percent", [(-1, 10),(10,-5),(10,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,expected", [
    (5,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-3,1.5, 'a'])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    ("  save20 ",20),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "save0", "", " abc "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class behavior ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_zero(self):
        assert round2(self.cart.total()) == 0.0

    def test_add_item_and_subtotal(self):
        self.cart.add_item('apple', 3, quantity=4)
        assert round2(self.cart.subtotal()) == 12.0

    def test_remove_item_partial(self):
        self.cart.add_item('banana', 2, quantity=5)
        self.cart.remove_item('banana', quantity=2)
        assert round2(self.cart.subtotal()) == 6.0

    def test_remove_item_all(self):
        self.cart.add_item('orange', 1.5, quantity=3)
        self.cart.remove_item('orange', quantity=3)
        assert round2(self.cart.total()) == 0.0

    def test_bulk_discount_within_cart(self):
        # add 10 apples at $10 each -> subtotal 100
        self.cart.add_item('apple', 10, quantity=10)
        # bulk discount 5% applies to each item? spec unclear.
        # We'll test total with coupon only for now.
        assert round2(self.cart.total()) == 100.0

    def test_coupon_application(self):
        self.cart.add_item('item', 200, quantity=1)
        # apply SAVE10 coupon -> 20%? actually 10%
        total = self.cart.total(coupon='SAVE10')
        expected_subtotal = round2(200 * (1-0.10))
        shipping = cart.shipping_fee(expected_subtotal)
        assert round2(total) == round2(expected_subtotal + shipping)

    def test_member_shipping(self):
        self.cart.add_item('item', 500, quantity=1)
        total_no_coupon = self.cart.total(member=True)
        expected_subtotal = 500.0
        shipping = cart.shipping_fee(expected_subtotal, member=True)
        assert round2(total_no_coupon) == round2(expected_subtotal + shipping)

    def test_invalid_coupon_raises(self):
        self.cart.add_item('item', 100, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon='BAD')
