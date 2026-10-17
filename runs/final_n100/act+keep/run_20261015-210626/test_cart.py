"""
# test_cart.py
import math
import pytest
import cart

# helper for approx with two decimals

def almost_equal(a, b):
    return abs(round(a, 2) - round(b, 2)) < 1e-9

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe5") == 5

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEX", "1234", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0.0
    assert cart.shipping_fee(999.99) == 60.0
    assert cart.shipping_fee(500, member=True) == 30.0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart methods -----------------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_basic(self):
        self.c.add_item("apple", 10, 2)
        assert self.c.items() == {"apple": 2}
        # subtotal should apply bulk discount: quantity=2 -> 0% discount
        assert almost_equal(self.c.subtotal(), 20.0)

    def test_add_same_item_increases_quantity(self):
        self.c.add_item("banana", 5, 3)
        self.c.add_item("banana", 5, 2)
        assert self.c.items() == {"banana": 5}
        # bulk discount: quantity=5 -> 0% (since <10)
        assert almost_equal(self.c.subtotal(), 25.0)

    def test_add_same_item_wrong_price_raises(self):
        self.c.add_item("orange", 7, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 8, 1)

    def test_remove_item(self):
        self.c.add_item("cherry", 3, 4)
        self.c.remove_item("cherry", 2)
        assert self.c.items() == {"cherry": 2}
        # remove more than remaining -> should remove item
        self.c.remove_item("cherry", 5)
        assert "cherry" not in self.c.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent", 1)

    def test_subtotal_with_bulk_discount(self):
        # 12 apples at $10 each -> bulk discount 5%
        self.c.add_item("apple", 10, 12)
        expected = 12 * 10 * (1 - 0.05)
        assert almost_equal(self.c.subtotal(), round(expected,2))

    def test_total_with_coupon_and_shipping(self):
        # Two items: 5 bananas at $2 each (no bulk discount) and 100 oranges at $1 each (15% discount)
        self.c.add_item("banana", 2, 5)
        self.c.add_item("orange", 1, 100)
        subtotal = 5*2 + 100*1
        # orange gets 15% off: 100*1*(0.85)=85; bananas no discount -> 10
        expected_subtotal = 10 + 85
        assert almost_equal(self.c.subtotal(), round(expected_subtotal,2))
        # apply coupon SAVE20 -> 20% off subtotal
        discounted = expected_subtotal * 0.8
        # shipping fee: subtotal after coupon is discounted (rounded)
        if discounted >= 1000:
            fee = 0
        else:
            fee = 60
        total_expected = discounted + fee
        assert almost_equal(self.c.total(coupon="SAVE20"), round(total_expected,2))

    def test_total_empty_cart_zero_no_shipping(self):
        assert self.c.total() == 0.0

    def test_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="invalid")

    def test_member_receives_half_shipping(self):
        # subtotal below 1000, member=True -> half fee
        self.c.add_item("item", 10, 1)
        assert almost_equal(self.c.total(member=True), 10 + 30.0)
"""
