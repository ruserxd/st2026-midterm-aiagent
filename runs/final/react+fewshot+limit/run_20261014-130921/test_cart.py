import pytest
import cart

# ----- apply_discount -----

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (100, 0),   # no discount
    (50, 100),  # full price removed
])
def test_apply_discount_edges(price, percent):
    expected = round(price * (1 - percent/100), 2)
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 10),
    (10, -5),
    (10, 110),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5") == 5
    assert cart.parse_coupon("   SaVe50   ") == 50

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "FOO10", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0


def test_shipping_fee_member_discount():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_initial(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0
        assert self.c.total() == 0

    def test_add_item_new(self):
        self.c.add_item("apple", 1.5, 2)
        assert self.c.items() == {"apple": 2}
        # subtotal: unit price * quantity with no bulk discount
        assert self.c.subtotal() == 3.0

    def test_add_item_existing_same_price(self):
        self.c.add_item("banana", 0.75, 5)
        self.c.add_item("banana", 0.75, 3)
        assert self.c.items() == {"banana": 8}
        # bulk discount for quantity 8 <10 -> no discount
        assert self.c.subtotal() == 6.0

    def test_add_item_existing_different_price(self):
        self.c.add_item("orange", 1.0, 2)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.5, 1)

    def test_add_item_invalid_parameters(self):
        with pytest.raises(ValueError):
            self.c.add_item("pear", -1, 1)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1, 0)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1, -3)

    def test_remove_item_partial(self):
        self.c.add_item("milk", 2.0, 4)
        self.c.remove_item("milk", 2)
        assert self.c.items() == {"milk": 2}
        # subtotal still 4.0 with no bulk discount
        assert self.c.subtotal() == 4.0

    def test_remove_item_complete(self):
        self.c.add_item("bread", 1.5, 3)
        self.c.remove_item("bread", 3)
        assert self.c.items() == {}
        assert self.c.subtotal() == 0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent", 1)

    def test_items_returns_copy(self):
        self.c.add_item("chicken", 5.0, 2)
        items = self.c.items()
        items["cheese"] = 10
        # original should not change
        assert "cheese" not in self.c.items()

    def test_subtotal_with_bulk_discount(self):
        # quantity 12 -> 5% discount on this item
        self.c.add_item("pen", 2.0, 12)
        expected = round(2.0 * 12 * (1 - 0.05), 2)
        assert self.c.subtotal() == expected

    def test_total_without_coupon_and_nonmember(self):
        # subtotal 2000 -> free shipping
        self.c.add_item("item", 1000, 2)
        assert self.c.total(member=False) == 2000.0

    def test_total_with_coupon_and_shipping(self):
        # subtotal 500 -> shipping 60; coupon 10% off
        self.c.add_item("gift", 250, 2)
        total = self.c.total(coupon="SAVE10")
        # subtotal after coupon: 500 * 0.9 = 450
        expected = round(450 + cart.shipping_fee(450), 2)
        assert total == expected

    def test_total_with_invalid_coupon(self):
        self.c.add_item("toy", 100, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="INVALID")

    def test_total_member_shipping_discount(self):
        # subtotal 800 -> shipping 60 normally, member gets 30
        self.c.add_item("book", 400, 2)
        total = self.c.total(member=True)
        expected = round(800 + cart.shipping_fee(800, member=True), 2)
        assert total == expected
