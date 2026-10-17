import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price
with pytest.raises(ValueError):
    cart.apply_discount(-10, 5)

# invalid percent
with pytest.raises(ValueError):
    cart.apply_discount(100, -1)
with pytest.raises(ValueError):
    cart.apply_discount(100, 101)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-5)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(3.7)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
with pytest.raises(ValueError):
    cart.parse_coupon("SAVE0")
with pytest.raises(ValueError):
    cart.parse_coupon("SAVEXX")
with pytest.raises(ValueError):
    cart.parse_coupon("HELLO10")

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),
    (50, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
with pytest.raises(ValueError):
    cart.shipping_fee(-5)

# ---------- Cart class behavior ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_subtotal_and_total(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_basic(self):
        self.cart.add_item("apple", 10, 3)
        assert self.cart.items() == {"apple": 3}
        # subtotal with bulk discount: 3 -> 5% off
        expected = cart.apply_discount(10 * 3, 5)
        assert self.cart.subtotal() == round(expected, 2)

    def test_add_same_item_increases_quantity(self):
        self.cart.add_item("banana", 2, 4)
        self.cart.add_item("banana", 2, 6)
        assert self.cart.items()["banana"] == 10
        # bulk discount for 10 -> 5%
        expected = cart.apply_discount(2 * 10, 5)
        assert self.cart.subtotal() == round(expected, 2)

    def test_add_item_different_price_raises(self):
        self.cart.add_item("orange", 3)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4)

    def test_remove_item_reduces_quantity_and_removes_when_zero(self):
        self.cart.add_item("mango", 5, 5)
        self.cart.remove_item("mango", 2)
        assert self.cart.items()["mango"] == 3
        self.cart.remove_item("mango", 3)
        assert "mango" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pineapple")

    def test_total_with_coupon_and_member_shipping(self):
        # 2 items: A(100*1), B(200*2)
        self.cart.add_item("A", 100, 1)
        self.cart.add_item("B", 200, 2)
        subtotal = cart.apply_discount(100 * 1 + 200 * 2, 0)  # no bulk discounts here
        total_after_coupon = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
        shipping = cart.shipping_fee(total_after_coupon, member=True)
        expected_total = round(total_after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == expected_total

    def test_total_without_coupon_member(self):
        self.cart.add_item("C", 300, 1)
        subtotal = cart.apply_discount(300 * 1, 0)
        shipping = cart.shipping_fee(subtotal, member=False)
        assert self.cart.total(member=False) == round(subtotal + shipping, 2)

    def test_total_no_shipping_for_free(self):
        self.cart.add_item("D", 500, 3)  # subtotal >1000 before coupon
        total = self.cart.total()
        # subtotal with bulk discount: 5% off because quantity=3<10
        expected_subtotal = cart.apply_discount(500 * 3, 0)
        assert expected_subtotal > 1000
        shipping = cart.shipping_fee(expected_subtotal, member=False)
        assert shipping == 60
        # no coupon applied
        assert total == round(expected_subtotal + shipping, 2)
