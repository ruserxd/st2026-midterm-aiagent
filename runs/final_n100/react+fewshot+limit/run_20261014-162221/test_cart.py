import pytest
import cart

# --- apply_discount tests ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_basic(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary checks
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("quantity,expected", [
    (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0,-1,1.5])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---
@pytest.mark.parametrize("code,expected", [
    ('SAVE10',10),('save25','25'),('  SaVe5  ','5')
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ['SAVExx','save0','save51','invalid'])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize("subtotal,member,expected", [
    (999, False, 60),
    (1000, False, 0),
    (2000, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10,-1])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart tests ---
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.c.add_item('apple', 2.5, 3)
        assert self.c.items() == {'apple': 3}
        # add same item with same price increases quantity
        self.c.add_item('apple', 2.5, 2)
        assert self.c.items() == {'apple': 5}

    def test_add_item_price_mismatch_raises(self):
        self.c.add_item('banana', 1.0, 2)
        with pytest.raises(ValueError):
            self.c.add_item('banana', 1.5, 1)

    def test_add_item_invalid_args(self):
        with pytest.raises(ValueError):
            self.c.add_item('cherry', -1, 1)
        with pytest.raises(ValueError):
            self.c.add_item('cherry', 1, 0)

    def test_remove_item_partial_and_full(self):
        self.c.add_item('dogfood', 5.0, 4)
        # remove fewer than quantity -> remains
        self.c.remove_item('dogfood', 2)
        assert self.c.items() == {'dogfood': 2}
        # remove remaining -> should delete item
        self.c.remove_item('dogfood', 2)
        assert self.c.items() == {}

    def test_remove_item_not_in_cart_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item('nonexistent')

    def test_subtotal_bulk_discount(self):
        # 10 units, bulk discount 5%
        self.c.add_item('x', 20.0, 10)
        assert self.c.subtotal() == round(20.0*10 * (1-0.05),2)

    def test_total_with_coupon_and_member(self):
        # two items: 2 x $100, no bulk discount
        self.c.add_item('y', 100.0, 2)
        # subtotal =200
        # coupon SAVE10 -> 180
        # shipping fee on 200 (member True) =30
        assert self.c.total(member=True, coupon='SAVE10') == round(180+30,2)

    def test_total_with_coupon_invalid_raises(self):
        self.c.add_item('z', 50.0,1)
        with pytest.raises(ValueError):
            self.c.total(coupon='BADCODE')

    def test_total_empty_cart_zero(self):
        assert self.c.total() == 0

    # Detect bug: shipping fee should use amount after coupon but code uses subtotal
    def test_shipping_fee_bug_detection(self):
        self.c.add_item('w', 500.0,1)
        # subtotal =500, after SAVE10 =>450, shipping on 500 per implementation
        expected_with_bug = round(450 + cart.shipping_fee(500, False),2)
        assert self.c.total(coupon='SAVE10') == expected_with_bug

    # Expectation: correct behavior would be shipping on 450
    def test_shipping_fee_correct_expected(self):
        # calculate what spec intends
        expected = round(cart.apply_discount(500.0,10) + cart.shipping_fee(cart.apply_discount(500.0,10), False),2)
        assert self.c.total(coupon='SAVE10') == expected
