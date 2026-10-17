import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.5, "a"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "10SAVE", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal, member, expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 2.0)
        assert self.cart.items() == {"apple": 3, "banana": 1}

    def test_add_existing_with_same_price(self):
        self.cart.add_item("apple", 1.5, 2)
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple": 5}

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("apple", 1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 2.0)

    def test_remove_item_and_quantity(self):
        self.cart.add_item("orange", 0.5, 4)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": 2}

    def test_remove_to_zero_removes_item(self):
        self.cart.add_item("pear", 1.2, 2)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist")

    def test_subtotal_with_bulk_discount(self):
        # 10 items -> 5% discount on each unit
        self.cart.add_item("widget", 20.0, 10)
        expected = 20.0 * 10 * (1 - 0.05)  # 190.0
        assert self.cart.subtotal() == round(expected, 2)

    def test_total_without_coupon(self):
        self.cart.add_item("item", 100.0)
        # subtotal 100, no bulk discount
        # subtotal after coupon (none) = 100
        # shipping for member False: 60 because <1000
        expected = round(100 + 60, 2)
        assert self.cart.total() == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 200.0)
        # subtotal 200, no bulk discount
        after_coupon = cart.apply_discount(200, 10)  # 180
        shipping = cart.shipping_fee(after_coupon, member=True)  # 30
        expected = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == expected
