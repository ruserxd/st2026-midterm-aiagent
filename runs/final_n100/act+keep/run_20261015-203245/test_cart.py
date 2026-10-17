import pytest
import cart

def round2(val):
    return round(float(val), 2)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount(price, percent, expected):
    assert round2(cart.apply_discount(price, percent)) == expected

# boundary conditions for raise ValueError
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_percent_out_of_bounds(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # corrected expected per spec
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.5, '10'])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize("code,expected", [
    ('SAVE10', 10),
    ('save20', 20),   # case‑insensitive per spec
    ('  SaVe30  ', 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    'SAVE0',      # below minimum
    'SAVE51',     # above maximum
    'DISCOUNT10',
    'SAVEX',
    '',
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initial_state(self):
        assert list(self.c.items()) == []
        assert self.c.subtotal() == 0
        assert round2(self.c.total()) == 60  # shipping fee applies when subtotal <1000 and no discounts

    def test_add_and_remove_items(self):
        self.c.add_item('apple', 100, 2)
        self.c.add_item('banana', 50, 3)
        assert self.c.subtotal() == 100*2 + 50*3
        # adding more apples
        self.c.add_item('apple', 100, 1)
        assert self.c.items()['apple'] == 3
        with pytest.raises(ValueError):
            self.c.add_item('apple', 90, 1)  # price mismatch

        # remove one banana
        self.c.remove_item('banana', 1)
        assert self.c.items()['banana'] == 2
        # remove remaining bananas
        self.c.remove_item('banana', 2)
        assert 'banana' not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item('pear')

    def test_total_with_member_and_coupon(self):
        self.c.add_item('widget', 200, 5)  # subtotal 1000
        total_no_discount = self.c.total(member=True)
        assert round2(total_no_discount) == 1000.0  # shipping free
        # apply coupon 10% off
        total_coupon = self.c.total(member=True, coupon='SAVE10')
        expected = 1000 * (1 - 0.10)  # bulk discount not applied because quantity<10
        assert round2(total_coupon) == expected

    def test_total_bulk_discount(self):
        self.c.add_item('item', 20, 12)  # quantity >=10 => bulk 5%
        subtotal = 20*12  # 240
        total = self.c.total()
        # apply bulk discount first: 240 *0.95=228 then shipping 60
        expected = round2(228 + 60)
        assert round2(total) == expected
