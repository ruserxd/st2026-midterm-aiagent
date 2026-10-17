import pytest
from cart import *

# Utility for rounding check

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_limits():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("q", [0, -5, 3.7])
def test_bulk_discount_errors(q):
    with pytest.raises(ValueError):
        bulk_discount_percent(q)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save20 ') == 20
    assert parse_coupon('  SaVe50   ') == 50

@ pytest.mark.parametrize("code", ['SAVE0', 'SAVEX', 'YES', '', 'SAVE51'])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item('apple', 2.0, 3)
        assert self.cart.items() == {'apple': 3}
        # Adding more increases quantity
        self.cart.add_item('apple', 2.0, 2)
        assert self.cart.items() == {'apple': 5}

    def test_add_conflicting_price(self):
        self.cart.add_item('banana', 1.5)
        with pytest.raises(ValueError):
            self.cart.add_item('banana', 1.6)

    def test_remove(self):
        self.cart.add_item('orange', 0.5, 4)
        self.cart.remove_item('orange', 2)
        assert self.cart.items() == {'orange': 2}
        self.cart.remove_item('orange', 2)
        assert 'orange' not in self.cart.items()

    def test_remove_not_in_cart(self):
        with pytest.raises(KeyError):
            self.cart.remove_item('pear')

    def test_subtotal_no_bulk_discount(self):
        self.cart.add_item('pen', 5, 2)
        # quantity <10 -> no bulk discount
        assert round2(self.cart.subtotal()) == round2(5*2)

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item('book', 20, 12)  # 5% discount
        expected = round2(20 * 12 * (1 - 0.05))
        assert round2(self.cart.subtotal()) == expected

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item('widget', 50, 10)  # bulk discount 5%
        subtotal = self.cart.subtotal()
        coupon_percent = parse_coupon('SAVE20')
        after_coupon = round2(subtotal * (1 - coupon_percent/100))
        fee = shipping_fee(after_coupon)
        total_expected = round2(after_coupon + fee)
        assert round2(self.cart.total(coupon='SAVE20')) == total_expected

    def test_total_member_shipping_half(self):
        self.cart.add_item('item', 200, 5)  # subtotal 1000 free shipping
        assert round2(self.cart.total(member=True)) == round2(1000)
        self.cart = Cart()
        self.cart.add_item('item', 50, 1)  # subtotal 50 -> fee 60, member 30
        assert round2(self.cart.total(member=True)) == round2(80)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
        assert self.cart.subtotal() == 0.0
