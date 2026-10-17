import pytest
import cart

# Helper to compare floats with rounding as specified
round2 = lambda x: round(x + 1e-12, 2)

# --- apply_discount tests ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert round2(cart.apply_discount(price, percent)) == round2(result)

# Invalid cases for apply_discount
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("qty,percent", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

# Invalid quantity
@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty)) if isinstance(qty, int) else cart.bulk_discount_percent(qty)

# --- parse_coupon tests ---
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEXY", "SAVE0", "SAVE51", "DISCOUNT10", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize("subtotal,fee", [
    (1000, 0),
    (1200, 0),
    (999.99, 60),
])
def test_shipping_non_member(subtotal, fee):
    assert cart.shipping_fee(subtotal) == fee

@pytest.mark.parametrize("subtotal,fee", [
    (999.99, 30),
    (500, 30),
])
def test_shipping_member(subtotal, fee):
    assert cart.shipping_fee(subtotal, member=True) == fee

# Invalid subtotal
@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ---
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_increase_qty_same_price(self):
        self.cart.add_item("banana", 0.8, 2)
        self.cart.add_item("banana", 0.8, 1)
        assert self.cart.items() == {"banana": 3}

    def test_add_item_same_name_different_price_error(self):
        self.cart.add_item("orange", 1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.5, 1)

    def test_remove_item_reduction(self):
        self.cart.add_item("milk", 3.0, 4)
        self.cart.remove_item("milk", 2)
        assert self.cart.items() == {"milk": 2}

    def test_remove_item_to_zero_removes(self):
        self.cart.add_item("bread", 2.5, 1)
        self.cart.remove_item("bread", 1)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("cheese", 1)

    def test_subtotal(self):
        self.cart.add_item("pen", 2.0, 5)   # 10.0
        self.cart.add_item("notebook", 5.0, 1)  # 5.0
        assert round2(self.cart.subtotal()) == round2(15.0)

    def test_total_no_coupon_non_member(self):
        self.cart.add_item("item", 1000.0, 1)
        # subtotal 1000 -> shipping free, no coupon
        assert round2(self.cart.total(member=False)) == round2(1000.0)

    def test_total_with_coupon_and_shipping_member(self):
        self.cart.add_item("gift", 200.0, 3)   # subtotal 600
        # apply coupon SAVE10 => discount 10%
        total = self.cart.total(member=True, coupon="SAVE10")
        expected = 600 * 0.9 + 30  # shipping 30 for member
        assert round2(total) == round2(expected)

    def test_total_empty_cart(self):
        assert round2(self.cart.total()) == 0.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("test", 50, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BAD")
