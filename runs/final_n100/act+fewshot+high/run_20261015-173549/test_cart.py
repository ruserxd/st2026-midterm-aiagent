import pytest
import cart

# ---------- Discount functions -------------------------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- Bulk discount -----------------------------------------------------

def test_bulk_discount_percent_boundaries():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 0
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

def test_bulk_discount_percent_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(2.3)

# ---------- Coupon parsing ----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe50  ") == 50

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")

# ---------- Shipping fee -------------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(500.5) == 60

def test_shipping_fee_member():
    assert cart.shipping_fee(999, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ---------- Cart class ---------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_items_and_totals(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("Apple", 1.5, quantity=3)
        assert self.cart.items() == {"Apple": 3}
        assert self.cart.subtotal() == 4.5

    def test_add_item_existing_same_price(self):
        self.cart.add_item("Banana", 0.8, quantity=2)
        self.cart.add_item("Banana", 0.8, quantity=1)
        assert self.cart.items() == {"Banana": 3}
        assert self.cart.subtotal() == 2.4

    def test_add_item_existing_different_price(self):
        self.cart.add_item("Orange", 1.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", 1.5, quantity=1)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("Grape", 2.0, quantity=4)
        self.cart.remove_item("Grape", quantity=2)
        assert self.cart.items() == {"Grape": 2}
        self.cart.remove_item("Grape", quantity=2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Pear")

    def test_total_with_coupon_and_shipping(self):
        # Add items: subtotal 200
        self.cart.add_item("Widget", 50, quantity=4)  # subtotal 200
        total_no_coup = self.cart.total()
        assert total_no_coup == 260.0  # 200 + shipping 60

        # Coupon SAVE10 (10% off)
        total_with_coupon = self.cart.total(coupon="SAVE10")
        discounted_amount = 200 * 0.90
        expected_total = round(discounted_amount + 60, 2)  # shipping on discounted amount still 60 because <1000
        assert total_with_coupon == expected_total

    def test_total_member_shipping(self):
        self.cart.add_item("Item", 20, quantity=5)  # subtotal 100
        total_non_member = self.cart.total()
        assert total_non_member == 160.0  # 100 + shipping 60

        total_member = self.cart.total(member=True)
        assert total_member == 130.0  # 100 + shipping 30

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
