import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases for apply_discount errors
@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,percent", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# Errors for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25 ", 25),
    ("  SaVe50", 50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "INVALID",
    "SAVE0",
    "SAVE51",
    "SAVEX10",
    "  ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,fee", [
    (0, 60),
    (500, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee(subtotal, fee):
    assert cart.shipping_fee(subtotal) == fee
    assert cart.shipping_fee(subtotal, member=True) == fee/2 if fee>0 else 0

# Errors for shipping_fee
@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": (1.0, 3)}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.5, 2)
        self.cart.add_item("banana", 0.5, 3)
        assert self.cart.items() == {"banana": (0.5, 5)}

    def test_add_item_existing_diff_price(self):
        self.cart.add_item("orange", 0.8, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.9, 2)

    def test_remove_item_partial(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": (1.5, 2)}

    def test_remove_item_all(self):
        self.cart.add_item("grape", 0.3, 2)
        self.cart.remove_item("grape", 2)
        assert "grape" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango", 1)

    def test_subtotal(self):
        self.cart.add_item("itemA", 10, 2)
        self.cart.add_item("itemB", 5, 3)
        assert self.cart.subtotal() == 10*2 + 5*3

    def test_total_non_member_no_coupon(self):
        self.cart.add_item("tshirt", 20, 2)  # subtotal 40
        total = self.cart.total()
        expected = 40 + cart.shipping_fee(40)
        assert total == expected

    def test_total_member_with_bulk_discount_and_coupon(self):
        # 100 units of a single item triggers bulk discount 15%
        self.cart.add_item("widget", 2, 100)  # subtotal 200
        total = self.cart.total(member=True, coupon="SAVE10")
        # bulk discount applied before shipping? assume yes
        discounted_subtotal = cart.apply_discount(200, cart.bulk_discount_percent(100))
        after_coupon = cart.apply_discount(discounted_subtotal, 10)
        fee = cart.shipping_fee(after_coupon, member=True)
        expected = round(after_coupon + fee, 2)
        assert total == expected

    def test_total_zero_items(self):
        assert self.cart.total() == 0.0
