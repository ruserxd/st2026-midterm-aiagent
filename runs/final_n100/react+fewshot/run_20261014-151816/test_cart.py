import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),     # no discount
    (50, 100, 0.0),      # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Boundary and error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),   # below 10
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "NOTACODE", ""])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal, expected", [
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_non_member(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart functionality
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items_initially_empty(self):
        assert list(self.cart.items()) == []

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, 3)
        items = list(self.cart.items())
        assert len(items) == 1
        name, unit_price, quantity = items[0]
        assert name == "apple"
        assert unit_price == 1.0
        assert quantity == 3

    def test_add_item_existing_same_price_increases_quantity(self):
        self.cart.add_item("banana", 0.5, 2)
        self.cart.add_item("banana", 0.5, 4)
        items = list(self.cart.items())
        assert len(items) == 1
        name, unit_price, quantity = items[0]
        assert quantity == 6

    def test_add_item_existing_different_price_raises(self):
        self.cart.add_item("orange", 0.8)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0)

    def test_remove_item_decreases_quantity_and_removes_when_zero(self):
        self.cart.add_item("grape", 2.0, 5)
        self.cart.remove_item("grape", 3)
        items = list(self.cart.items())
        assert items[0][2] == 2
        self.cart.remove_item("grape", 2)
        assert list(self.cart.items()) == []

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_calculation(self):
        self.cart.add_item("pen", 1.5, 2)
        self.cart.add_item("notebook", 3.0, 1)
        assert self.cart.subtotal() == pytest.approx(6.0)

    def test_total_without_member_or_coupon(self):
        self.cart.add_item("item", 200, 5)  # subtotal 1000, free shipping
        assert self.cart.total() == pytest.approx(1000.0)

    def test_total_with_shipping_and_nonmember(self):
        self.cart.add_item("toy", 50, 2)  # subtotal 100, fee 60
        assert self.cart.total() == pytest.approx(160.0)

    def test_total_with_member_discount_and_coupon(self):
        # 1 item: bulk discount 5% because quantity 10
        self.cart.add_item("widget", 10.0, 10)  # subtotal 100
        # member gets half shipping fee: 30
        # coupon SAVE20 -> 20%
        total = self.cart.total(member=True, coupon="SAVE20")
        # subtotal after bulk discount: 100 * (1-0.05)=95
        # coupon on that subtotal: 95*(1-0.2)=76
        # shipping fee for subtotal 100 is 60, member pays 30
        expected = 76 + 30
        assert total == pytest.approx(expected)
