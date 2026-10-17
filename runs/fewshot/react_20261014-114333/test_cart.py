import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Invalid inputs for apply_discount
@pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (50, 150)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
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

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe30   ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "", "10SAVE"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,expected", [
    (500, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_regular(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal,expected", [
    (500, 30),
    (800, 30),
])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new(self):
        self.c.add_item("apple", 2.5, 3)
        assert self.c.items() == {"apple": (2.5, 3)}

    def test_add_item_existing_same_price(self):
        self.c.add_item("banana", 1.0, 2)
        self.c.add_item("banana", 1.0, 4)
        assert self.c.items() == {"banana": (1.0, 6)}

    def test_add_item_existing_different_price(self):
        self.c.add_item("orange", 3.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 4.0, 2)

    def test_remove_item_partial(self):
        self.c.add_item("pear", 2.0, 5)
        self.c.remove_item("pear", 3)
        assert self.c.items() == {"pear": (2.0, 2)}

    def test_remove_item_entire(self):
        self.c.add_item("grape", 4.0, 4)
        self.c.remove_item("grape", 4)
        assert "grape" not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("mango", 1)

    def test_subtotal_and_total_member_coupon(self):
        # Items: 2 apples at 100 each, 3 bananas at 50 each
        self.c.add_item("apple", 100.0, 2)  # subtotal 200
        self.c.add_item("banana", 50.0, 3)  # subtotal 150
        assert self.c.subtotal() == 350.0
        # No bulk discount applied (quantities below thresholds)
        expected_total = 350.0 + cart.shipping_fee(350.0, member=True)
        assert self.c.total(member=True) == expected_total

    def test_total_with_coupon_and_bulk_discount(self):
        # 12 oranges at 10 each - subtotal 120
        self.c.add_item("orange", 10.0, 12)
        # Bulk discount 5% applies to subtotal
        bulk_disc = cart.apply_discount(120.0, 5)  # 114.0
        coupon_percent = cart.parse_coupon("SAVE20")
        final_after_coupon = cart.apply_discount(bulk_disc, coupon_percent)
        expected_total = final_after_coupon + cart.shipping_fee(120.0)
        assert self.c.total(coupon="SAVE20") == expected_total
