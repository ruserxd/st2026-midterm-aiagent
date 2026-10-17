import re
import pytest
import cart

# ---------- helpers ----------

# Use the specification for expected values
expected_apply_discount = {
    (200, 15): 170.0,
    (100, 0): 100.0,
    (50, 100): 0.0,
}

# test apply_discount
@pytest.mark.parametrize("price,percent,expected", [
    *[(k[0], k[1], v) for k, v in expected_apply_discount.items()],
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

# invalid cases
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
expected_bulk = {
    0: 0,
    5: 0,
    10: 5,
    50: 10,
    100: 15,
    200: 15,
}
@pytest.mark.parametrize("quantity,expected", list(expected_bulk.items()))
def test_bulk_discount_percent(quantity, expected):
    if quantity <= 0:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(quantity)
    else:
        assert cart.bulk_discount_percent(quantity) == expected

# ---------- parse_coupon ----------
valid_codes = {
    'SAVE10': 10,
    'save10': 10,
    ' SAVE20 ': 20,
    'SaVe50': 50,
}
@staticmethod
def check_parse(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code,expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVExx", "10SAVE", "123", "", "  ", "SAVE51"]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@staticmethod
def check_shipping(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -500])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item('apple', 1.0, 3)
        self.c.add_item('banana', 0.5)
        assert self.c.items() == {
            'apple': (1.0, 3),
            'banana': (0.5, 1),
        }

    def test_remove_item(self):
        self.c.add_item('orange', 2.0, 5)
        self.c.remove_item('orange', 2)
        assert self.c.items()['orange'] == (2.0, 3)
        # remove more than exists should remove all
        self.c.remove_item('orange', 10)
        assert 'orange' not in self.c.items()

    def test_subtotal(self):
        self.c.add_item('pen', 1.5, 4)   # 6.0
        self.c.add_item('paper', 2.0)    # 2.0
        assert self.c.subtotal() == pytest.approx(8.0)

    def test_total_no_discounts(self):
        self.c.add_item('book', 20.0, 2)   # subtotal 40
        total = self.c.total(member=False, coupon=None)
        expected_subtotal = 40.0
        shipping = cart.shipping_fee(expected_subtotal)
        assert total == pytest.approx(expected_subtotal + shipping)

    def test_total_with_bulk_discount(self):
        # 12 apples at $5 each => subtotal 60, bulk discount 5%
        self.c.add_item('apple', 5.0, 12)
        expected_subtotal = 60.0 * (1 - cart.bulk_discount_percent(12)/100)
        shipping = cart.shipping_fee(expected_subtotal)
        total = self.c.total()
        assert total == pytest.approx(expected_subtotal + shipping)

    def test_total_with_coupon_and_member(self):
        # 10 pencils at $1 each => subtotal 10, coupon SAVE10 -> 10%
        self.c.add_item('pencil', 1.0, 10)
        total = self.c.total(member=True, coupon='SAVE10')
        discount = cart.parse_coupon('SAVE10') / 100
        discounted_subtotal = 10 * (1 - discount)
        shipping = cart.shipping_fee(discounted_subtotal, member=True)
        assert total == pytest.approx(discounted_subtotal + shipping)

    def test_total_invalid_coupon(self):
        self.c.add_item('gift', 5.0)
        with pytest.raises(ValueError):
            self.c.total(coupon='INVALID')

    def test_total_invalid_member_flag(self):
        # member flag must be boolean; implementation may accept others
        # Specification not explicit, but we test that non-boolean raises TypeError
        if isinstance(cart.Cart().total.__code__.co_freevars, set):
            pass  # skip check due to ambiguity
        else:
            self.c.add_item('gift', 5.0)
            with pytest.raises(TypeError):
                self.c.total(member='yes')
