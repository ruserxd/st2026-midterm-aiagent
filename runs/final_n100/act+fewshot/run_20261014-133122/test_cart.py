import pytest
import cart

# ---------- helper functions for rounding checks ----------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full free
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid_arguments(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk discount tests ----------
@pytest.mark.parametrize("qty, expected", [
    (9, 0),   # <10
    (10, 5),  # 10-49
    (50, 10), # 50-99
    (100, 15),# >=100
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEX", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (1200, True, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_totals(self):
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0
        assert self.cart.items() == {}

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.00, 3)
        self.cart.add_item("banana", 0.50, 2)
        # adding same name with same price increases quantity
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple":5, "banana":2}

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -0.5, 3)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.5, 0)
        # price mismatch
        self.cart.add_item("pear", 1.00, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 2.00, 1)

    def test_remove_and_auto_delete(self):
        self.cart.add_item("milk", 3.00, 4)
        self.cart.remove_item("milk", 2)
        assert self.cart.items() == {"milk":2}
        # remove remaining quantity
        self.cart.remove_item("milk", 2)
        assert "milk" not in self.cart.items()
        # removing non‑existent item raises KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("bread", 1)

    def test_subtotal_bulk_discount(self):
        # 12 apples at $2 each -> bulk discount 5% => 24 * 0.95 = 22.8
        self.cart.add_item("apple", 2.00, 12)
        assert self.cart.subtotal() == pytest.approx(22.80, rel=1e-9)
        # 60 bananas at $1 each -> bulk discount 10% => 60 * 0.90 = 54
        self.cart.add_item("banana", 1.00, 60)
        assert self.cart.subtotal() == pytest.approx(22.80 + 54, rel=1e-9)

    def test_total_with_coupon_and_shipping(self):
        # items: 5 books at $20 => bulk discount 0% -> 100
        self.cart.add_item("book", 20.00, 5)
        subtotal = self.cart.subtotal()
        assert subtotal == 100.0
        # apply coupon SAVE10 -> 90
        total_with_coupon = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
        # shipping for non‑member: 60 => final 150
        expected_total = round(total_with_coupon + cart.shipping_fee(total_with_coupon), 2)
        assert self.cart.total(coupon="SAVE10") == expected_total
        # member should pay half shipping on the amount after coupon
        expected_member_shipping = cart.shipping_fee(total_with_coupon, member=True)
        assert self.cart.total(member=True, coupon="SAVE10") == round(total_with_coupon + expected_member_shipping, 2)

    def test_total_no_items(self):
        # empty cart should cost zero and no shipping
        assert self.cart.total() == 0.0

    def test_invalid_coupon_in_total(self):
        self.cart.add_item("item", 10.00, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
