import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (10, 33, 6.7),          # 10 * 0.67 = 6.7
    (50, 0, 50.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "ten"])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save10", 10),
    (" SAVE20 ", 20),
    ("SaVe5", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", ["SAVE0", "SAVE51", "BAD10", "12345", "", " SAVE"])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50.5])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple": 3}
        assert self.cart.subtotal() == pytest.approx(3.0)

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 2.5, quantity=2)
        self.cart.add_item("banana", 2.5, quantity=1)
        assert self.cart.items() == {"banana": 3}
        assert self.cart.subtotal() == pytest.approx(7.5)

    def test_add_item_existing_different_price(self):
        self.cart.add_item("orange", 1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.0)

    def test_add_item_invalid_inputs(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, quantity=-3)

    def test_remove_item(self):
        self.cart.add_item("milk", 1.5, quantity=4)
        self.cart.remove_item("milk", quantity=2)
        assert self.cart.items() == {"milk": 2}
        self.cart.remove_item("milk", quantity=2)
        assert self.cart.items() == {}

    def test_remove_item_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_bulk_discount(self):
        # 15 apples at $10 each -> bulk discount 5%
        self.cart.add_item("apple", 10.0, quantity=15)
        expected = round(10.0 * 15 * (1 - 5 / 100), 2)  # 142.5
        assert self.cart.subtotal() == pytest.approx(expected)

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("book", 50.0, quantity=3)  # subtotal = 150
        subtotal = self.cart.subtotal()
        coupon_percent = cart.parse_coupon("SAVE10")
        subtotal_after_coupon = cart.apply_discount(subtotal, coupon_percent)
        shipping = cart.shipping_fee(subtotal_after_coupon, member=False)
        expected_total = round(subtotal_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == pytest.approx(expected_total)

    def test_total_member_shipping(self):
        self.cart.add_item("widget", 200.0, quantity=1)  # subtotal = 200
        expected_no_coupon = round(200 + cart.shipping_fee(200, member=False), 2)
        assert self.cart.total() == pytest.approx(expected_no_coupon)

        expected_member_shipping = round(200 + cart.shipping_fee(200, member=True), 2)
        assert self.cart.total(member=True) == pytest.approx(expected_member_shipping)

    def test_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BAD10")
