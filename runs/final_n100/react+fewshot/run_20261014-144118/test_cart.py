import pytest
import cart

# Helper for rounding as per spec: using round(value,2)

def approx(val):
    return round(val, 2)

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),      # example
    (100, 0, 100.0),       # no discount
    (100, 100, 0.0),       # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Invalid price and percent
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (9, 0),   # below 10
    (10, 5),  # 10-49
    (49, 5),
    (50, 10), # 50-99
    (99, 10),
    (100, 15),# 100+
    (200, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "", "SAVE0", "SAVE51", "INVALID", "1234", "SAVExx",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (999.99, False, 60),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, 3)
        assert self.cart.items() == {"apple": 3}
        # unit price must match; try adding same item with different price -> error
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 3.0, 1)

    def test_add_item_existing(self):
        self.cart.add_item("banana", 1.0, 2)
        self.cart.add_item("banana", 1.0, 4)
        assert self.cart.items() == {"banana": 6}

    def test_remove_item_partial(self):
        self.cart.add_item("cherry", 0.5, 10)
        self.cart.remove_item("cherry", 3)
        assert self.cart.items() == {"cherry": 7}

    def test_remove_item_complete(self):
        self.cart.add_item("date", 1.2, 4)
        self.cart.remove_item("date", 4)
        assert "date" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("fig", 1)

    def test_subtotal_basic(self):
        # Bulk discount applies: 10 units of item -> 5% off
        self.cart.add_item("grape", 3.0, 10)  # subtotal before discount 30
        expected = round(30 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_multiple(self):
        self.cart.add_item("honey", 5.0, 50)   # bulk 10% -> 200 * 0.9 = 180
        self.cart.add_item("icecream", 2.0, 99) # bulk 10% -> 198 * 0.9 = 178.2
        total_expected = round(180 + 178.2, 2)
        assert self.cart.subtotal() == total_expected

    def test_total_no_coupon_member(self):
        # Subtotal $1000 -> free shipping, member discount not applied yet
        self.cart.add_item("item", 200.0, 5)   # 5 units no bulk: 1000
        assert self.cart.total(member=True) == 1000.0

    def test_total_with_coupon(self):
        self.cart.add_item("lamp", 50.0, 10)  # 10 units -> 5% bulk: 500 * 0.95 = 475
        # Coupon SAVE10 => 10%
        amount_after_coupon = round(475 * (1 - 0.10), 2)
        shipping = cart.shipping_fee(amount_after_coupon, member=False)
        expected_total = round(amount_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0

    def test_total_invalid_coupon(self):
        self.cart.add_item("pen", 1.0, 2)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
