import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Edge cases for invalid input
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (99, 10),
    (50, 10),
    (49, 5),
    (10, 5),
    (9, 0),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    ("  SaVe20  ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "abc10", ""])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_new_item(self):
        self.cart.add_item("apple", 2.5, 3)
        assert self.cart.items() == {"apple": (2.5, 3)}

    def test_add_existing_item_increases_quantity(self):
        self.cart.add_item("banana", 1.0, 2)
        self.cart.add_item("banana", 1.0, 4)
        assert self.cart.items() == {"banana": (1.0, 6)}

    def test_add_existing_item_different_price_raises(self):
        self.cart.add_item("orange", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4.0, 2)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("pear", 2.0, 5)
        self.cart.remove_item("pear", 3)
        assert self.cart.items() == {"pear": (2.0, 2)}
        self.cart.remove_item("pear", 2)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango", 1)

    def test_subtotal(self):
        self.cart.add_item("a", 10.0, 2)  # 20
        self.cart.add_item("b", 5.0, 3)   # 15
        assert self.cart.subtotal() == 35

    def test_total_no_discount(self):
        self.cart.add_item("x", 100.0, 1)
        assert self.cart.total() == 160  # subtotal 100 + shipping 60

    def test_total_with_member_shipping(self):
        self.cart.add_item("y", 200.0, 1)
        assert self.cart.total(member=True) == 230

    def test_total_with_coupon(self):
        self.cart.add_item("z", 50.0, 4)  # subtotal 200
        assert self.cart.total(coupon="SAVE10") == 240

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("w", 500.0, 1)
        assert self.cart.total(member=True, coupon="SAVE5") == 505

    def test_total_coupon_invalid_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
