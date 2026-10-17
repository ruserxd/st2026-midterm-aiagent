import pytest
import cart

# Helper for rounding checks

def approx_equal(a, b):
    return round(a - b, 2) == 0

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

with pytest.raises(ValueError):
    cart.apply_discount(-10, 10)
with pytest.raises(ValueError):
    cart.apply_discount(10, -5)
with pytest.raises(ValueError):
    cart.apply_discount(10, 105)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5  # spec: >=10 =>5%
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(250) == 15

with pytest.raises(ValueError):
    cart.bulk_discount_percent(-1)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(0.5)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("   SaVe50") == 50

with pytest.raises(ValueError):
    cart.parse_coupon("SAVEX")
    cart.parse_coupon("SAVE0")
    cart.parse_coupon("SAVE51")
    cart.parse_coupon("DIS10")
    cart.parse_coupon("SAVE ")

# ---------- shipping_fee ----------

def test_shipping_fee():
    # free shipping for subtotal >= 1000
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    # member pays half of standard fee
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(200, member=False) == 60

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_and_items(self):
        self.cart.add_item("apple", 5, 3)
        assert self.cart.items() == {"apple": 3}
        self.cart.add_item("apple", 5, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_different_price_error(self):
        self.cart.add_item("banana", 2, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 3, 1)

    def test_remove_and_auto_removal(self):
        self.cart.add_item("orange", 4, 5)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": 3}
        self.cart.remove_item("orange", 3)  # should remove entirely
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("apple", 2, 10)   # bulk 5%
        self.cart.add_item("banana", 1, 45)  # bulk 10%
        expected = round(19 + 40.5, 2)
        assert self.cart.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("item", 200, 6)
        subtotal = self.cart.subtotal()
        assert subtotal == 1200.00
        total_after_coupon = cart.apply_discount(subtotal, 20)  # 960
        shipping = cart.shipping_fee(total_after_coupon)
        assert shipping == 0
        assert approx_equal(self.cart.total(coupon="SAVE20"), round(total_after_coupon + shipping, 2))

    def test_total_member_shipping(self):
        self.cart.add_item("item", 100, 3)  # subtotal 300
        total = self.cart.total(member=True)
        assert approx_equal(total, 330.0)
