import pytest
import cart

# Helper function to compare floats with rounding

def approx(value, expected):
    return round(value, 2) == round(expected, 2)

# Tests for apply_discount
@ pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@ pytest.mark.parametrize("price,percent", [
    (-10, 10),
    (50, -5),
    (60, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@ pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@ pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    ("  SaVe50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@ pytest.mark.parametrize("code", [
    "SAV10",
    "SAVE0",
    "SAVE51",
    "abc10",
    " SAVE -5 ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@ pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert list(self.cart.items()) == []
        assert self.cart.subtotal() == 0.0

    def test_add_item(self):
        self.cart.add_item("Apple", 100, 3)
        items = list(self.cart.items())
        assert len(items) == 1
        name, unit_price, quantity = items[0]
        assert name == "Apple"
        assert unit_price == 100
        assert quantity == 3
        assert self.cart.subtotal() == 300.0

    def test_remove_item(self):
        self.cart.add_item("Banana", 50, 5)
        self.cart.remove_item("Banana", 2)
        items = list(self.cart.items())
        name, unit_price, quantity = items[0]
        assert quantity == 3
        self.assertRaises(KeyError, lambda: self.cart.remove_item("Apple", 1))

    def test_total_member_coupon(self):
        # Add items with bulk discount
        self.cart.add_item("ItemA", 200, 10)   # 5% bulk
        self.cart.add_item("ItemB", 100, 60)   # 10% bulk
        subtotal = self.cart.subtotal()
        assert subtotal == 200*10 + 100*60
        total_before_discount = subtotal
        # Apply coupon SAVE20
        total_with_coupon = cart.apply_discount(total_before_discount, cart.parse_coupon("SAVE20"))
        expected_total = total_with_coupon + cart.shipping_fee(subtotal, member=True)
        assert self.cart.total(member=True, coupon="SAVE20") == pytest.approx(expected_total)

    def test_total_non_member_no_coupon(self):
        self.cart.add_item("Item", 500, 2)  # no bulk discount
        subtotal = 1000.0
        shipping = cart.shipping_fee(subtotal)
        assert self.cart.total(member=False, coupon=None) == pytest.approx(subtotal + shipping)
