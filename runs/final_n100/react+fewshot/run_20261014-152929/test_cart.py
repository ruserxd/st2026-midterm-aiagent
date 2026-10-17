import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_success(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-10, 5), (10, -1), (10, 101)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (55, 10),
    (120, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE50 ", 50),
])
def test_parse_coupon_valid(code, expected):
    # Implementation accepts case-insensitive and whitespace
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["",
    "SAVExx",
    "SAVE0",
    "SAVE51",
    "OTHER10",
    "  ",])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_zero_and_no_shipping(self):
        assert self.cart.total() == 0.0

    def test_add_item_updates_items_and_subtotal(self):
        self.cart.add_item("apple", 1.20, quantity=3)
        # items() returns dict of name -> quantity
        assert self.cart.items() == {"apple": 3}
        assert self.cart.subtotal() == pytest.approx(3 * 1.20)

    def test_remove_item_decrements_quantity_and_updates_subtotal(self):
        self.cart.add_item("banana", 0.50, quantity=5)
        self.cart.remove_item("banana", quantity=2)
        assert self.cart.items() == {"banana": 3}
        assert self.cart.subtotal() == pytest.approx(1.5)

    def test_remove_more_than_exists_removes_item(self):
        self.cart.add_item("orange", 2.00, quantity=1)
        self.cart.remove_item("orange", quantity=2)
        assert "orange" not in self.cart.items()

    def test_total_with_coupon_and_shipping_member(self):
        # add items to exceed $1000 subtotal for free shipping test later
        self.cart.add_item("expensive", 500, quantity=3)  # subtotal = 1500
        total = self.cart.total(member=True, coupon="SAVE10")
        expected_after_discount = 1500 * 0.90
        expected_shipping = 0 if expected_after_discount >= 1000 else (30 if True else 60)
        assert total == pytest.approx(expected_after_discount + expected_shipping)

    def test_total_with_invalid_coupon_raises(self):
        self.cart.add_item("item", 10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_no_shipping_on_small_order_member_flag_effective(self):
        # subtotal $200 -> shipping 30 for member
        self.cart.add_item("item", 200, quantity=1)
        total = self.cart.total(member=True)
        assert total == pytest.approx(200 + 30)

    def test_total_non_member_shipping_fee(self):
        # subtotal $200 -> shipping 60 for non-member
        self.cart.add_item("item", 200, quantity=1)
        total = self.cart.total(member=False)
        assert total == pytest.approx(200 + 60)
