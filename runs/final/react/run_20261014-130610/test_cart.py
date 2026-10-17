import math
import cart
import pytest

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price, percent",
    [
        (100, 0),   # no discount
        (100, 100), # full price paid
        (123.45, 25),
    ],
)
def test_apply_discount_various(price, percent):
    expected = round(price * (1 - percent / 100), 2)
    assert cart.apply_discount(price, percent) == expected

# Value errors for invalid arguments
@pytest.mark.parametrize("price", [-1, -10.5])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent -------------------------------------------

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_negative_or_zero(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" SAVE50 ") == 50
    assert cart.parse_coupon(" SaVe1 ") == 1

@pytest.mark.parametrize(
    "code",
    [
        "",
        "SAV10",          # missing S
        "SAVE0",           # below range
        "SAVE51",          # above range
        "SAVE-5",          # negative
        " SAVE 10 ",       # space inside code
        "SAVEABC",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 100, quantity=2)
        self.cart.add_item("banana", 150)   # default quantity 1
        assert self.cart.items() == {
            "apple": (100, 2),
            "banana": (150, 1),
        }

    def test_add_existing_item(self):
        self.cart.add_item("soda", 120, quantity=3)
        self.cart.add_item("soda", 120, quantity=2)
        assert self.cart.items()["soda"] == (120, 5)

    def test_remove_item(self):
        self.cart.add_item("milk", 200, quantity=4)
        self.cart.remove_item("milk", quantity=1)
        assert self.cart.items()["milk"] == (200, 3)

    def test_remove_more_than_exists(self):
        self.cart.add_item("bread", 80, quantity=2)
        with pytest.raises(ValueError):
            self.cart.remove_item("bread", quantity=5)

    def test_subtotal_and_total_non_member_no_coupon(self):
        self.cart.add_item("item1", 500, quantity=2)   # subtotal 1000
        assert self.cart.subtotal() == 1000
        total = self.cart.total(member=False)
        assert total == 1000 + cart.shipping_fee(1000)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item2", 300, quantity=3)   # subtotal 900
        total_before = self.cart.total()
        # member free shipping -> 30 fee. Coupon discount applied after subtotal? assume apply before shipping.
        expected_subtotal = 900
        discounted = cart.apply_discount(expected_subtotal, 10)
        shipping = cart.shipping_fee(discounted, member=True)
        expected_total = round(discounted + shipping, 2)
        assert total_before == expected_total

    def test_bulk_discount_in_total(self):
        # buying 100 units triggers 15% bulk discount on that item's price before subtotal calculation.
        self.cart.add_item("bulkitem", 200, quantity=120)  # base price per unit 200
        # Apply bulk discount percent
        bulk_percent = cart.bulk_discount_percent(120)
        discounted_unit_price = cart.apply_discount(200, bulk_percent)
        expected_subtotal = round(discounted_unit_price * 120, 2)
        assert math.isclose(self.cart.subtotal(), expected_subtotal, abs_tol=0.01)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

# End of tests
