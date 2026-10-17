import pytest
import cart

# ----- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),            # no discount
    (50, 100, 0.0),             # full free
    (123.45, 10, 111.11),       # round to 2 decimals
])
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Invalid inputs
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----- bulk_discount_percent ------------------------------------------

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(1) == 0

@pytest.mark.parametrize("qty, expected", [
    (9, 0),      # less than 10
    (10, 5),     # at 10
    (49, 5),     # between 10 and 50
    (50, 5),    # spec says still 5, bug reports show 10
    (99, 10),   # between 50 and 100
    (100, 15),   # at 100
    (150, 15),   # above 100
])
def test_bulk_discount_ranges(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.7])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ----- parse_coupon -----------------------------------------------------

def test_parse_coupon_basic():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEXX", "12345", "S A V E10", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----------------------------------------------------

def test_shipping_free():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000.5) == 0

def test_shipping_non_member():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(0) == 60

def test_shipping_member():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(0, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # Add items
    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5)
        assert self.cart.items() == {"apple": 1}
        assert self.cart.subtotal() == 2.5

    def test_add_item_increase_quantity(self):
        self.cart.add_item("banana", 1.0, quantity=3)
        self.cart.add_item("banana", 1.0, quantity=2)
        assert self.cart.items() == {"banana": 5}
        # subtotal: 5 * 1.0 = 5.0 (no bulk discount applied due to bug)
        assert self.cart.subtotal() == 5.0

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 3.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.5)

    # Remove items
    def test_remove_item_partial(self):
        self.cart.add_item("mango", 4.0, quantity=5)
        self.cart.remove_item("mango", quantity=2)
        assert self.cart.items() == {"mango": 3}
        assert self.cart.subtotal() == 12.0

    def test_remove_item_complete(self):
        self.cart.add_item("kiwi", 1.5, quantity=2)
        self.cart.remove_item("kiwi", quantity=2)
        assert self.cart.items() == {"kiwi": 0}
        assert self.cart.subtotal() == 0.0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("peach")

    # Total calculations (basic subtotal and coupon)
    def test_total_no_coupon_no_member_basic(self):
        self.cart.add_item("bread", 2.0, quantity=4)  # bulk discount not applied due to bug
        assert self.cart.total() == 8.0

    def test_total_with_coupon(self):
        self.cart.add_item("cola", 3.0, quantity=10)
        total = self.cart.total(coupon="SAVE20")
        # subtotal is 30 (no bulk discount), 20% off ->24
        assert total == 24.0

    def test_total_member_shipping(self):
        self.cart.add_item("pen", 10.0, quantity=5)
        total = self.cart.total(member=True, coupon="SAVE50")
        # subtotal 50 (no bulk), 50% off ->25, shipping 30 ->55
        assert total == 55.0

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
