import cart
import pytest

# Helper to round consistently
round2 = lambda x: round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price,percent", [(-10, 5), (20, -1), (30, 101)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25 ") == 25
    assert cart.parse_coupon("  SaVe50") == 50

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOPE", "SAVEX", "  ", "SAVEDO"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # member discount
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(2000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.cart.add_item("Apple", 5.0, quantity=2)
        assert self.cart.items() == {"Apple": 2}
        # adding same item increases quantity
        self.cart.add_item("Apple", 5.0, quantity=3)
        assert self.cart.items() == {"Apple": 5}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("Banana", 1.2)
        with pytest.raises(ValueError):
            self.cart.add_item("Banana", 1.5)

    def test_remove_item(self):
        self.cart.add_item("Orange", 3, quantity=4)
        # remove less than existing
        self.cart.remove_item("Orange", quantity=2)
        assert self.cart.items() == {"Orange": 2}
        # remove remaining
        self.cart.remove_item("Orange", quantity=2)
        assert self.cart.items() == {}
        # removing nonexistent item raises KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("Orange")

    def test_subtotal_bulk_discount(self):
        # 5 units, no bulk discount
        self.cart.add_item("Pen", 2.0, quantity=5)
        assert round2(self.cart.subtotal()) == 10.00
        # add another item with bulk threshold
        self.cart.add_item("Notebook", 3.0, quantity=12)  # 5% discount
        subtotal = self.cart.subtotal()
        # Notebook: 12 * 3 = 36 - 5% = 34.2
        expected = round2(10 + 34.2)
        assert subtotal == pytest.approx(expected, rel=1e-9)

    def test_total_no_coupon(self):
        self.cart.add_item("Widget", 50, quantity=3)  # 3 items, no bulk
        total = self.cart.total()
        # Subtotal: 150, no discount, shipping fee 60 -> 210
        assert round2(total) == 210.00

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("Gadget", 200, quantity=1)
        subtotal = self.cart.subtotal()
        assert subtotal == 200
        total = self.cart.total(member=True, coupon="SAVE10")
        # Coupon 10% off: 180, shipping half of 60 -> 30, total 210
        assert round2(total) == 210.00

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
        assert self.cart.total(member=True) == 0
        assert self.cart.total(coupon="SAVE5") == 0

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
