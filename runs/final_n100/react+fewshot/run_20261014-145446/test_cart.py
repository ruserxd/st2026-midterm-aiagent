import pytest
import cart

# ---------- apply_discount --------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# edge cases for rounding
@pytest.mark.parametrize("price,percent,result", [
    (99.9999, 10, 89.99991),  # should round to 2 decimals -> 90.00
])
def test_apply_discount_rounding(price, percent, result):
    assert cart.apply_discount(price, percent) == round(result, 2)

# invalid inputs
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -------------------------------------------
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

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["NOSAVE10", "SAVE0", "SAVE51", "save-5", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initially(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", unit_price=2.5, quantity=3)
        assert self.cart.items()["apple"] == (2.5, 3)
        # adding same item should increase quantity
        self.cart.add_item("apple", unit_price=2.5, quantity=2)
        assert self.cart.items()["apple"] == (2.5, 5)

    def test_remove_item(self):
        self.cart.add_item("banana", unit_price=1.0, quantity=5)
        # remove fewer than existing
        self.cart.remove_item("banana", quantity=2)
        assert self.cart.items()["banana"] == (1.0, 3)
        # removing more than exists should raise
        with pytest.raises(KeyError):
            self.cart.remove_item("banana", quantity=5)
        # remove remaining fully
        self.cart.remove_item("banana", quantity=3)
        assert "banana" not in self.cart.items()

    def test_subtotal_and_total(self):
        self.cart.add_item("item1", 100.0, 2)  # subtotal 200
        self.cart.add_item("item2", 50.0, 5)   # subtotal +250 = 450
        assert self.cart.subtotal() == 450.0
        # total without coupon or member should equal subtotal + shipping
        assert self.cart.total() == 450.0 + cart.shipping_fee(450.0)
        # member discount: bulk discounts per item apply before total
        self.cart.add_item("item3", 10.0, 12)   # quantity >=10 -> 5% discount on these units
        subtotal = 450.0 + (10.0 * 12 * 0.95)
        assert self.cart.subtotal() == pytest.approx(subtotal)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("widget", unit_price=200, quantity=50)  # bulk discount 10%
        # subtotal after bulk discount: 200*50*0.9 = 9000
        expected_subtotal = 200 * 50 * 0.90
        assert self.cart.subtotal() == pytest.approx(expected_subtotal)
        # apply coupon SAVE20 => 20% off on subtotal
        total_after_coupon = expected_subtotal * (1 - 0.20)
        shipping = cart.shipping_fee(total_after_coupon, member=True)  # member pays half
        final_total = total_after_coupon + shipping
        assert self.cart.total(member=True, coupon="SAVE20") == pytest.approx(final_total)
