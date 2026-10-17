import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "10"])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,percent", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "INVALID", "1234", "SAVEXY"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_items_and_subtotal_and_total(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.00
        assert self.c.total() == 0

    def test_add_item_basic(self):
        self.c.add_item("apple", 2.5, 3)
        assert self.c.items() == {"apple": 3}
        # subtotal should consider bulk discount: quantity=3 <10 -> no discount
        assert self.c.subtotal() == round(2.5*3, 2)

    def test_add_item_existing_same_price(self):
        self.c.add_item("banana", 1.0, 2)
        self.c.add_item("banana", 1.0, 3)
        assert self.c.items() == {"banana": 5}
        # subtotal with quantity=5 -> bulk discount 0
        assert self.c.subtotal() == round(1.0*5, 2)

    def test_add_item_existing_different_price_raises(self):
        self.c.add_item("orange", 1.5, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 2.0, 1)

    def test_remove_item_partial_and_removal(self):
        self.c.add_item("pear", 3.0, 4)
        self.c.remove_item("pear", 2)
        assert self.c.items() == {"pear": 2}
        # remove more than remaining: should delete item
        self.c.remove_item("pear", 5)  # line[1] becomes -3, triggers deletion
        assert "pear" not in self.c.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent")

    def test_total_with_coupon_and_shipping(self):
        # Add items that trigger bulk discount
        self.c.add_item("item", 100.0, 10)  # quantity=10 -> 5% discount on line total
        subtotal = round(100.0*10*(1-0.05), 2)
        assert self.c.subtotal() == subtotal
        # Apply coupon SAVE20 (20% off after subtotal)
        total_with_coupon = cart.apply_discount(subtotal, 20)
        # Shipping fee for member (subtotal after coupon <1000) -> 30
        expected_total = round(total_with_coupon + 30, 2)
        assert self.c.total(member=True, coupon="SAVE20") == expected_total
