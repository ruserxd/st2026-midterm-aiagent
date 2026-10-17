import pytest
import cart

# --- tests for parse_coupon ---------------------------------

def test_parse_valid_coupons():
    # Basic valid coupon
    assert cart.parse_coupon("SAVE10") == 10
    # Case-insensitive and whitespace ignored as per spec
    assert cart.parse_coupon("  save20 ") == 20


def test_parse_invalid_coupons():
    with pytest.raises(ValueError):
        cart.parse_coupon("BAD10")
    with pytest.raises(ValueError):
        # percent out of allowed range
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX")

# --- tests for apply_discount ---------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(1000, 5) == 950.0


def test_apply_discount_invalid_inputs():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 105)

# --- tests for bulk_discount_percent --------------------------

def test_bulk_discount_percent():
    # No discount for low quantity
    assert cart.bulk_discount_percent(9) == 0
    # 5% for 10-49 items as per spec
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # 10% for 50-99 items
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    # 15% for 100+ items
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# --- tests for shipping_fee ---------------------------------

def test_shipping_fee_free_and_member(monkeypatch):
    # subtotal >= threshold => free shipping
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500, member=True) == 0

    # subtotal < threshold => base fee
    assert cart.shipping_fee(200) == 60
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(999.99) == 60
    # members pay half the base fee
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(0, member=True) == 30


def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# --- tests for Cart functionality -----------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_and_subtotal(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_no_bulk_discount(self):
        self.cart.add_item("Widget", unit_price=100, quantity=3)
        # subtotal = 300 (no bulk discount for qty<10)
        assert self.cart.subtotal() == 300
        # total: no coupon, shipping 60 -> 360
        assert self.cart.total() == 360.0

    def test_bulk_discount_and_total(self):
        # 10 units => 5% bulk discount per spec
        self.cart.add_item("Gadget", unit_price=100, quantity=10)
        # discounted price per unit = 95, subtotal = 950
        assert self.cart.subtotal() == 950.0
        # total: shipping fee on 950 -> 60, final = 1010
        assert self.cart.total() == 1010.0

    def test_coupon_and_total(self):
        self.cart.add_item("Thing", unit_price=200, quantity=5)
        subtotal_before = 1000
        # apply coupon SAVE10: discount 100
        discounted = cart.apply_discount(subtotal_before, 10)  # 900
        # shipping fee on discounted amount (since subtotal<1000) -> 60
        expected_total = discounted + cart.shipping_fee(discounted)
        assert self.cart.total(coupon="SAVE10") == pytest.approx(expected_total)
        # invalid coupon should raise ValueError
        with pytest.raises(ValueError):
            self.cart.total(coupon="BAD10")

    def test_member_shipping(self):
        self.cart.add_item("Large", unit_price=300, quantity=4)  # subtotal 1200 free shipping
        assert self.cart.total(member=True) == 1200.0
        # reduce to trigger non-free shipping but member pays half
        self.cart.remove_item("Large", quantity=1)
        # now subtotal = 300, shipping fee half of base =>30
        expected_total = 300 + 30
        assert self.cart.total(member=True) == pytest.approx(expected_total)

    def test_add_and_remove_items(self):
        self.cart.add_item("Pen", unit_price=5, quantity=2)
        self.cart.add_item("Notebook", unit_price=10, quantity=1)
        assert len(self.cart.items()) == 2
        # remove one Pen -> one remaining with qty 1
        self.cart.remove_item("Pen", quantity=1)
        pen = next(item for item in self.cart.items() if item[0] == "Pen")
        assert pen[2] == 1
        # remove the last Pen entirely
        self.cart.remove_item("Pen")
        items_names = [item[0] for item in self.cart.items()]
        assert "Pen" not in items_names
        assert len(self.cart.items()) == 1

# ----------------------------------------------------------------
