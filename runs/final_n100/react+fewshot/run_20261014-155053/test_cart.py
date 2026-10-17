import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_basic():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("   SAVE5  ") == 5

@pytest.mark.parametrize("code", ["SAVEX", "savex", "", "SAVE0", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

assert cart.shipping_fee(200, member=True) == 30
assert cart.shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ------------------------------------------------------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.50, 3)
        assert self.cart.items() == {"apple": 3}
        # unit price check via subtotal calculation
        expected = cart.apply_discount(1.5 * 3, cart.bulk_discount_percent(3))
        assert self.cart.subtotal() == round(expected, 2)

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.75, 2)
        self.cart.add_item("banana", 0.75, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_existing_diff_price_raises(self):
        self.cart.add_item("orange", 1.00, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.90, 2)

    def test_remove_partial_and_complete(self):
        self.cart.add_item("mango", 2.00, 5)
        self.cart.remove_item("mango", 3)
        assert self.cart.items() == {"mango": 2}
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_total_with_coupon_and_shipping_member(self):
        # Items: 2 apples at $10 each => subtotal 20, no bulk discount
        self.cart.add_item("apple", 10.00, 2)
        # Apply coupon SAVE5 (5%) and member shipping half fee
        total = self.cart.total(member=True, coupon="SAVE5")
        # Step1: subtotal 20
        # Step2: apply 5% discount => 19.0
        # Step3: shipping on 19.0 -> member => 30 (since <1000)
        expected = round(19.0 + 30, 2)
        assert total == expected

    def test_total_no_items(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

# ---------- End of tests ----------------------------------------------------"
