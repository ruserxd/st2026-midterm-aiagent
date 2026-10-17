import pytest
import cart

# Helper functions and parametrizations
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Invalid discount parameters should raise ValueError
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Bulk discount percentages according to spec
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),  # updated expected per specification
    (99, 10),
    (100, 15),
    (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid quantity for bulk discount should raise ValueError
@pytest.mark.parametrize("quantity", [0, -5, 3.2, "10"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Coupon parsing (case-insensitive and whitespace trimmed) – spec expects valid
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupons – should raise ValueError
@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "ABC123", "", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee logic according to spec
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
    (400, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# Shipping fee with negative subtotal should raise ValueError
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        # add items and check items dict returned by Cart.items()
        self.cart.add_item("apple", 1.00, quantity=3)
        self.cart.add_item("banana", 0.50)
        items_dict = self.cart.items()
        assert len(items_dict) == 2
        assert items_dict["apple"] == 3
        assert items_dict["banana"] == 1

    def test_remove_item(self):
        self.cart.add_item("milk", 2.00, quantity=5)
        # remove fewer than existing
        self.cart.remove_item("milk", quantity=2)
        items = self.cart.items()
        assert items["milk"] == 3
        # removing more than remaining should delete the entry entirely
        self.cart.remove_item("milk", quantity=5)
        assert "milk" not in self.cart.items()

    def test_subtotal(self):
        self.cart.add_item("book", 12.99, quantity=2)  # subtotal 25.98
        self.cart.add_item("pen", 1.50)
        assert pytest.approx(self.cart.subtotal(), rel=1e-9) == 27.48

    def test_total_no_coupon_no_member(self):
        self.cart.add_item("item", 200, quantity=3)  # subtotal 600
        # No coupon; non-member shipping 60
        assert pytest.approx(self.cart.total(), rel=1e-9) == 660.00

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("widget", 50, quantity=20)  # subtotal 1000
        # After coupon SAVE10: 1000 * 0.90 = 900
        discounted_subtotal = cart.apply_discount(1000, cart.parse_coupon("SAVE10"))
        shipping = cart.shipping_fee(discounted_subtotal, member=True)
        expected_total = round(discounted_subtotal + shipping, 2)
        assert pytest.approx(self.cart.total(member=True, coupon="SAVE10"), rel=1e-9) == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.00

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
