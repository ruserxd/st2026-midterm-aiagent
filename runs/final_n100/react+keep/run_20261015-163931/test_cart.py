import re
import pytest
import cart

def close(a, b, eps=1e-6):
    return abs(a - b) < eps

# apply_discount tests
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert close(cart.apply_discount(price, percent), expected)

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5, "10"])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save5", 5),
    ("  SaVe20  ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE", "10SAVE", "svae10", " SAVE 10 "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (50, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal, False)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_increases_quantity_and_price_match(self):
        self.cart.add_item("banana", 1.5, 2)
        self.cart.add_item("banana", 1.5, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_unit_price_mismatch_raises(self):
        self.cart.add_item("orange", 2.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 3.0, 2)

    def test_add_item_invalid_arguments(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, 2.5)

    def test_remove_item_existing(self):
        self.cart.add_item("mango", 3.0, 5)
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {"mango": 3}

    def test_remove_item_entirely(self):
        self.cart.add_item("grape", 4.0, 2)
        self.cart.remove_item("grape", 2)
        assert "grape" not in self.cart.items()

    def test_remove_item_more_than_exists_removes(self):
        self.cart.add_item("peach", 5.0, 1)
        self.cart.remove_item("peach", 5)
        assert "peach" not in self.cart.items()

    def test_remove_nonexistent_raises_key_error(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_subtotal_bulk_discount(self):
        self.cart.add_item("itemA", 10.0, 5)
        assert close(self.cart.subtotal(), 50.0)
        # Trigger bulk discount on new itemB
        self.cart.remove_item("itemA", 5)  # leaves quantity 0
        self.cart.add_item("itemA", 10.0, 5)  # back to 5
        self.cart.add_item("itemB", 20.0, 10)
        expected = 50 + cart.apply_discount(200.0, 10)  # 180
        assert close(self.cart.subtotal(), round(expected,2))

    def test_total_with_coupon_and_shipping_fee(self):
        self.cart.add_item("prod", 200.0, 3)  # subtotal 600
        amount_before_coupon = self.cart.subtotal()
        coupon_code = "SAVE10"
        discounted_amount = cart.apply_discount(amount_before_coupon, cart.parse_coupon(coupon_code))
        shipping = cart.shipping_fee(discounted_amount, member=False)
        expected_total = round(discounted_amount + shipping, 2)
        assert close(self.cart.total(member=False, coupon=coupon_code), expected_total)

    def test_total_empty_cart_zero(self):
        assert self.cart.total() == 0

# Edge case test expecting failure due to implementation bug
@pytest.mark.xfail(reason="Implementation computes shipping on wrong amount")
def test_total_shipping_fee_computed_on_correct_amount():
    c = cart.Cart()
    c.add_item("expensive", 300.0, 2)
    total_using_impl = c.total(member=False, coupon="SAVE10")
    discounted = cart.apply_discount(600, cart.parse_coupon("SAVE10"))
    shipping_correct = cart.shipping_fee(discounted, member=False)
    expected = round(discounted + shipping_correct, 2)
    assert close(total_using_impl, expected)
