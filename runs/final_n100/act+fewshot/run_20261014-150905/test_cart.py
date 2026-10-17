import pytest
import cart

# ---- Tests for helper functions -----

@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (123.45, 10, 111.11),  # round to two decimals
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity, expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "",
    "SAVE0",
    "SAVE51",
    "DISCOUNT10",
    " SAVE10x ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (999.99, False, 60),
    (200, True, 30),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Tests for Cart class -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart(self):
        assert self.cart.items() == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_and_remove_item(self):
        self.cart.add_item("apple", 1.5, quantity=3)
        self.cart.add_item("banana", 0.75)
        assert len(self.cart.items()) == 2
        # subtotal: 3*1.5 + 0.75 = 4.5 + 0.75 = 5.25
        assert self.cart.subtotal() == 5.25
        # remove one apple
        self.cart.remove_item("apple", quantity=1)
        assert len(self.cart.items()) == 2
        # subtotal should now be 2*1.5 + 0.75 = 3.75
        assert self.cart.subtotal() == 3.75
        # remove remaining apples
        self.cart.remove_item("apple", quantity=2)
        assert len(self.cart.items()) == 1
        assert self.cart.subtotal() == 0.75

    def test_remove_nonexistent_item(self):
        with pytest.raises(ValueError):
            self.cart.remove_item("pear")

    def test_total_with_coupon_and_shipping(self):
        # add items: 10 bananas at $2 each -> subtotal 20
        self.cart.add_item("banana", 2.0, quantity=10)
        # bulk discount percent for 10 items is 5%
        # but coupon applies after bulk? spec says total uses coupon, shipping on amount after coupon.
        # We'll test with coupon SAVE10 -> 10% off
        total = self.cart.total(coupon="SAVE10")
        # subtotal 20, coupon 10% => 18.0, shipping fee (subtotal>=1000? no) -> 60
        assert total == round(18.0 + 60, 2)

    def test_total_member_shipping(self):
        self.cart.add_item("item", 50, quantity=20)  # subtotal 1000
        # member gets free shipping because subtotal >=1000
        assert self.cart.total(member=True) == round(1000.0 + 0, 2)

    def test_total_invalid_coupon(self):
        self.cart.add_item("foo", 10)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
