import pytest
import cart

# ----- apply_discount -----
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),      # example from spec
        (100, 0, 100.0),       # no discount
        (100, 100, 0.0),       # full discount
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (50, -5), (30, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
valid_cases = {
    "SAVE10": 10,
    "save20": 20,
    " SAVE30 ": 30,
}
for code, exp in valid_cases.items():
    def _test(code=code, exp=exp):
        assert cart.parse_coupon(code) == exp
    globals()[f"test_parse_coupon_{code.strip().replace(' ', '_')}"] = _test

@pytest.mark.parametrize(
    "invalid",
    ["SAV10", "SAVE0", "SAVE51", "abc", "SAVE-5", 123],
)
def test_parse_coupon_invalid(invalid):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid)

# ----- shipping_fee -----
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_totals_zero(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_and_remove_item(self):
        self.cart.add_item("apple", 1.0, quantity=5)
        assert self.cart.items() == {"apple": 5}
        # subtotal: bulk discount for 5 units => 0%, so 5*1.0
        assert self.cart.subtotal() == 5.0

        self.cart.remove_item("apple", quantity=3)
        assert self.cart.items() == {"apple": 2}
        # subtotal now: 2*1.0 = 2.0
        assert self.cart.subtotal() == 2.0

    def test_add_existing_item_same_price(self):
        self.cart.add_item("banana", 0.5, quantity=10)
        self.cart.add_item("banana", 0.5, quantity=15)
        assert self.cart.items() == {"banana": 25}
        # bulk discount for 25 -> 5% => 25*0.5*0.95
        expected = round(25 * 0.5 * 0.95, 2)
        assert self.cart.subtotal() == expected

    def test_add_existing_item_different_price_raises(self):
        self.cart.add_item("cherry", 1.5)
        with pytest.raises(ValueError):
            self.cart.add_item("cherry", 2.0)

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear")

    def test_total_with_coupon_and_shipping(self):
        # Add items to trigger bulk discount and shipping >0
        self.cart.add_item("widget", 20.0, quantity=50)  # bulk 10% discount
        # Subtotal: 50*20*0.9 = 900.0
        assert self.cart.subtotal() == 900.0
        # Coupon SAVE5 => 5% off on subtotal => 855.0
        total_after_coupon = 900.0 * 0.95
        # Shipping for non-member: fee 60
        expected_total = round(total_after_coupon + 60, 2)
        assert self.cart.total(coupon="SAVE5") == expected_total

    def test_total_no_shipping_on_free(self):
        self.cart.add_item("expensive", 100.0, quantity=11)  # subtotal > 1000 after discount
        assert self.cart.subtotal() >= 1100  # >1000 before shipping
        total = self.cart.total()
        # Shipping should be 0 because subtotal >=1000
        expected_total = round(self.cart.subtotal(), 2)
        assert total == expected_total

    def test_total_member_half_shipping(self):
        self.cart.add_item("costly", 20.0, quantity=10)  # bulk 5% => 190.0
        # subtotal 190 < 1000 so shipping 60; member pays half 30
        assert cart.shipping_fee(190, member=True) == 30
        total = self.cart.total(member=True)
        expected_total = round(cart.subtotal() + 30, 2)
        assert total == expected_total

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 10.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
