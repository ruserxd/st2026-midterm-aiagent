import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "save51", "abc10", " SAVE -5 "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60.0
    assert cart.shipping_fee(999.99) == 60.0
    assert cart.shipping_fee(1000) == 0.0
    assert cart.shipping_fee(1200) == 0.0

@ pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.00, 3)
        assert self.c.items() == {"apple": 3}
        # adding same item increases quantity
        self.c.add_item("apple", 1.00, 2)
        assert self.c.items() == {"apple": 5}
        # adding another item
        self.c.add_item("banana", 0.50)
        assert self.c.items() == {"apple": 5, "banana": 1}

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item("orange", -1, 2)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 0.99, 0)
        # mismatch unit price
        self.c.add_item("pear", 0.80, 1)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 0.90, 2)

    def test_remove_and_items(self):
        self.c.add_item("tshirt", 20.00, 3)
        self.c.remove_item("tshirt", 1)
        assert self.c.items() == {"tshirt": 2}
        # remove all
        self.c.remove_item("tshirt", 2)
        assert self.c.items() == {}

    def test_remove_not_in_cart(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent")

    def test_subtotal_and_bulk_discount(self):
        # 5 apples at $1 each -> no bulk discount
        self.c.add_item("apple", 1.00, 5)
        assert self.c.subtotal() == 5.0
        # 10 oranges at $2 -> 5% discount per orange
        self.c.add_item("orange", 2.00, 10)
        expected_orange = round(2.00 * 10 * (1 - 0.05), 2)
        assert abs(self.c.subtotal() - (5.0 + expected_orange)) < 1e-6

    def test_total_with_coupon_and_shipping(self):
        # subtotal of $120 -> no bulk discount, coupon 10%
        self.c.add_item("item", 30.00, 4)
        assert self.c.subtotal() == 120.0
        total = self.c.total(coupon="SAVE10")
        # after coupon: 108, shipping 60 => 168
        assert total == 168.0
        # member gets half shipping
        total_member = self.c.total(coupon="SAVE10", member=True)
        assert total_member == 138.0
        # no coupon
        assert self.c.total() == 180.0  # 120 + 60
        # empty cart cost 0
        empty = cart.Cart()
        assert empty.total() == 0

    def test_total_invalid_coupon(self):
        self.c.add_item("item", 10.00, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BAD")
