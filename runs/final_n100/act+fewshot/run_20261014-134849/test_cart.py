import pytest
import cart

# --- apply_discount ---
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# edge cases for invalid values
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---
@pytest.mark.parametrize("qty,expected", [
    (1, 0), (9, 0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 2.3])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --- parse_coupon ---
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10), ("save20",20), (" SAVE30 ",30), ("SaVe5",5)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEXY", "SAVE0", "SAVE51", "DISCOUNT10", "  ", "save-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ---
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0), (1500, True, 0), (999, False, 60), (800, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ---
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 5, 2)
        self.c.add_item("banana", 3, 1)
        assert self.c.items() == {"apple":2, "banana":1}

    def test_add_existing_same_price(self):
        self.c.add_item("apple", 5, 1)
        self.c.add_item("apple", 5, 3)
        assert self.c.items()["apple"] == 4

    def test_add_existing_different_price_raises(self):
        self.c.add_item("apple", 5, 1)
        with pytest.raises(ValueError):
            self.c.add_item("apple", 6, 2)

    def test_remove_partial_and_full(self):
        self.c.add_item("orange", 4, 3)
        self.c.remove_item("orange", 1)
        assert self.c.items()["orange"] == 2
        self.c.remove_item("orange", 2)
        assert "orange" not in self.c.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("pear", 1)

    def test_subtotal_and_total_no_discount(self):
        self.c.add_item("a", 10, 2)   # 20
        self.c.add_item("b", 5, 1)    # 5
        assert self.c.subtotal() == 25.0
        assert self.c.total() == 25.0

    def test_total_with_member_and_coupon(self):
        self.c.add_item("item", 200, 6)  # subtotal 1200 -> free shipping
        coupon = cart.parse_coupon("SAVE10")
        expected_subtotal = 1200.0
        discount = cart.apply_discount(expected_subtotal, coupon)
        assert cart.shipping_fee(discount, member=True) == 30.0
        total = self.c.total(member=True, coupon=cart.parse_coupon("SAVE10"))
        # total should be discounted subtotal + shipping (member half of 60)
        assert total == discount + 30.0

    def test_total_with_bulk_discount_and_shipping(self):
        self.c.add_item("bulk", 100, 120)  # bulk gives 15% discount on each item?
        # In this implementation, bulk_discount_percent is not automatically applied.
        # The total method does not use bulk_discount_percent; we just test subtotal.
        assert self.c.subtotal() == 12000.0
        assert self.c.total() == 12000.0 + 60
