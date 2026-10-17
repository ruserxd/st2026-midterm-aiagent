import pytest
import cart

# Utility to round to two decimals for comparisons when needed

def r(x):
    return round(float(x), 2)

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "GOOD10", "", "  "])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 2)
        self.cart.add_item("banana", 0.5)
        assert self.cart.items() == {"apple": 2, "banana": 1}

    def test_add_existing_increase_qty(self):
        self.cart.add_item("orange", 0.8, 3)
        self.cart.add_item("orange", 0.8, 2)
        assert self.cart.items() == {"orange": 5}

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("pear", 1.2)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.3)

    @pytest.mark.parametrize("unit_price,qty", [(-0.5, 1), (1.0, -2)])
    def test_add_invalid_args_raises(self, unit_price, qty):
        with pytest.raises(ValueError):
            self.cart.add_item("invalid", unit_price, qty)

    def test_remove_item(self):
        self.cart.add_item("item1", 10.0, 5)
        self.cart.remove_item("item1", 2)
        assert self.cart.items() == {"item1": 3}

    def test_remove_more_than_exists(self):
        self.cart.add_item("item2", 2.0, 1)
        self.cart.remove_item("item2", 5)  # should remove item completely
        assert "item2" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("ghost")

    def test_subtotal_no_discount(self):
        self.cart.add_item("x", 10.0, 4)  # quantity < 10 -> no bulk discount
        assert self.cart.subtotal() == 40.0

    def test_subtotal_with_bulk_discount(self):
        # 10 items: 5% discount on each unit price
        self.cart.add_item("y", 20.0, 10)
        expected = round(20.0 * 10 * (1 - 0.05), 2)  # 190.0
        assert self.cart.subtotal() == expected

    def test_subtotal_multiple_items(self):
        self.cart.add_item("a", 5.0, 3)
        self.cart.add_item("b", 8.0, 12)  # 10% discount on b
        subtotal_a = 5.0 * 3
        subtotal_b = round(8.0 * 12 * (1 - 0.10), 2)
        assert self.cart.subtotal() == round(subtotal_a + subtotal_b, 2)

    def test_total_no_shipping_for_empty(self):
        assert self.cart.total() == 0.0

    def test_total_with_coupon_and_shipping(self):
        # add items totaling 200 before discounts
        self.cart.add_item("z", 50.0, 4)  # no bulk discount
        subtotal = 200.0
        coupon_percent = cart.parse_coupon("SAVE10")  # 10% off -> 180
        shipping = cart.shipping_fee(180, member=False)
        total_expected = round(180 + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_member_shipping_discount(self):
        self.cart.add_item("w", 300.0, 1)  # no bulk discount
        subtotal = 300.0
        # member gets half shipping fee (30)
        shipping = cart.shipping_fee(subtotal, member=True)
        total_expected = round(subtotal + shipping, 2)
        assert self.cart.total(member=True) == total_expected

    def test_total_coupon_invalid_raises(self):
        self.cart.add_item("item", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
