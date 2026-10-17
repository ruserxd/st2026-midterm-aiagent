import pytest
import cart

# Utility function for checking exceptions

def assert_raises(exc_type, func, *args, **kwargs):
    with pytest.raises(exc_type) as excinfo:
        func(*args, **kwargs)
    return excinfo.value

# ----- bulk_discount_percent tests -----
@pytest.mark.parametrize("quantity,expected", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -10, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    assert_raises(ValueError, cart.bulk_discount_percent, quantity)

# ----- apply_discount tests -----
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (1000, 0, 1000.0),
    (1000, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_invalid(price):
    assert_raises(ValueError, cart.apply_discount, price, 10)

@pytest.mark.parametrize("percent", [-5, 105, 200])
def test_apply_discount_percent_invalid(percent):
    assert_raises(ValueError, cart.apply_discount, 100, percent)

# ----- parse_coupon tests -----
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save10", 10),
    ("  SAVE25   ", 25),
    ("SaVe50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "NOTA", "SAVEXX", "SAVEE", "  "])
def test_parse_coupon_invalid(code):
    assert_raises(ValueError, cart.parse_coupon, code)

# ----- shipping_fee tests -----
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (50, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee_valid(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    assert_raises(ValueError, cart.shipping_fee, subtotal, False)

# ----- Cart class tests -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty_cart(self):
        assert self.cart.items() == []
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_and_subtotal(self):
        self.cart.add_item("widget", unit_price=20, quantity=3)
        assert self.cart.items() == [("widget", 20, 3)]
        assert self.cart.subtotal() == 60.0

    def test_bulk_discount_application(self):
        self.cart.add_item("gadget", unit_price=100, quantity=12)
        assert self.cart.subtotal() == 1140.0

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("item", unit_price=200, quantity=1)
        assert self.cart.total(coupon="SAVE10") == 240.0

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0

    def test_total_member_free_shipping_over_1000(self):
        self.cart.add_item("expensive", unit_price=500, quantity=3)
        assert self.cart.total(member=True) == 1500.0

    def test_invalid_coupon_raises(self):
        self.cart.add_item("foo", 10, 1)
        assert_raises(ValueError, self.cart.total, False, "INVALID")
