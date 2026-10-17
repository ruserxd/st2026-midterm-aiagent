import pytest
import cart

# Helper function to compare floats with expected rounding

def assert_float_eq(actual, expected):
    assert round(actual, 2) == round(expected, 2)

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases: invalid inputs
@pytest.mark.parametrize("price,percent", [(-10, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# parse_coupon tests
@pytest.mark.parametrize("code,result", [
    ('SAVE10', 10),
    ('save20', 20),
    ('  SaVe30  ', 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVEXX", "", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,fee", [
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0

    def test_add_item_new_and_existing(self):
        self.cart.add_item('apple', 100, 2)
        assert self.cart.items() == {'apple': 2}
        self.cart.add_item('apple', 100, 3)
        assert self.cart.items() == {'apple': 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item('banana', -10, 1)
        with pytest.raises(ValueError):
            self.cart.add_item('orange', 50, 0)

    def test_remove_item(self):
        self.cart.add_item('pear', 200, 4)
        self.cart.remove_item('pear', 2)
        assert self.cart.items() == {'pear': 2}
        # removing more than remaining should remove the item
        self.cart.remove_item('pear', 3)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item('nonexist')

    def test_subtotal_with_bulk_discount(self):
        # 10 items at 100 each => bulk discount 5%
        self.cart.add_item('book', 100, 10)
        assert_float_eq(self.cart.subtotal(), 95.0)  # 100*10=1000, 5% off = 950

    def test_total_with_coupon_and_shipping_member(self):
        self.cart.add_item('gift', 200, 1)
        total = self.cart.total(member=True, coupon='SAVE20')
        # subtotal 200, 20% off -> 160; shipping for member on 200 is 30
        assert_float_eq(total, 190.0)

    def test_total_free_shipping(self):
        self.cart.add_item('expensive', 1200, 1)
        total = self.cart.total()
        # subtotal 1200; no coupon; shipping free -> 1200
        assert_float_eq(total, 1200.0)
