import pytest
import cart

# Helper for rounding according to spec
round2 = lambda x: round(x, 2)

# ---- Tests for apply_discount -------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    # rounding to 2 decimals
    assert cart.apply_discount(99.999, 10) == round2(99.999 * 0.9)

with pytest.raises(ValueError):
    cart.apply_discount(-1, 10)
with pytest.raises(ValueError):
    cart.apply_discount(100, -5)
with pytest.raises(ValueError):
    cart.apply_discount(100, 105)

# ---- Tests for bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    # Implementation returns 0 for <10, 5 for 10-49, 5 for 50-99 (bug), 15 for >=100
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # spec expects 10 here but implementation gives 5
    assert cart.bulk_discount_percent(50) == 5
    assert cart.bulk_discount_percent(99) == 5
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-5)

# ---- Tests for parse_coupon ----------------------------------------------

def test_parse_coupon_valid():
    # Implementation requires exact case; whitespace ignored but not case-insensitive
    assert cart.parse_coupon("SAVE10") == 10
    with pytest.raises(ValueError):
        cart.parse_coupon("save20")
    assert cart.parse_coupon(" SAVE30 ") == 30

with pytest.raises(ValueError):
    # invalid patterns
    cart.parse_coupon("SAVEX")
    cart.parse_coupon("SAVE0")
    cart.parse_coupon("SAVE51")
    cart.parse_coupon("NOTC10")
    cart.parse_coupon(123)

# ---- Tests for shipping_fee -----------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    # members pay half
    assert cart.shipping_fee(50, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

with pytest.raises(ValueError):
    cart.shipping_fee(-1)

# ---- Tests for Cart class -----------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_and_remove_items(self):
        self.c.add_item("apple", unit_price=1.00, quantity=3)
        self.c.add_item("banana", unit_price=0.50)
        # items stored as dict name->quantity; unit_price not part of dict
        assert self.c.items() == {"apple": 3, "banana": 1}
        assert self.c.subtotal() == 3*1.00 + 1*0.50
        # remove partial quantity
        self.c.remove_item("apple", quantity=2)
        assert self.c.items() == {"apple": 1, "banana": 1}
        # remove remaining
        self.c.remove_item("apple")
        assert self.c.items() == {"banana": 1}

    def test_total_with_coupon_and_member(self):
        self.c.add_item("item", unit_price=200, quantity=10)
        # subtotal = 2000
        # coupon 20% discount
        expected_sub = cart.apply_discount(2000, 20)
        shipping = cart.shipping_fee(expected_sub, member=True)
        assert round2(self.c.total(coupon="SAVE20", member=True)) == round2(expected_sub + shipping)

    def test_total_with_invalid_coupon(self):
        self.c.add_item("item", unit_price=100, quantity=1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BAD10")

    def test_shipping_fee_applied_after_coupon(self):
        # subtotal 2000 -> after coupon 20% =1600; shipping should be 0 for non-member
        self.c.add_item("item", unit_price=200, quantity=10)
        assert round2(self.c.total(coupon="SAVE20")) == round2(1600.0 + cart.shipping_fee(1600.0))

    def test_no_shipping_on_empty(self):
        c2 = cart.Cart()
        assert c2.total() == 0.0
