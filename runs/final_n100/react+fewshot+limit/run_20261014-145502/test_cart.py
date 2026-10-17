import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0)
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected", [
    (99, 5), (49, 10), (199, 15), (1, 0)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_percent_error(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25 ", 25),
    ("  SaVe50", 50)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "NOTVALID"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple": 3}
        assert self.cart.subtotal() == 4.5

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 0.8, 2)
        self.cart.add_item("banana", 0.8, 1)
        assert self.cart.items() == {"banana": 3}
        assert self.cart.subtotal() == 2.4

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("orange", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.2, 1)

    def test_remove_partial_and_total(self):
        self.cart.add_item("milk", 2.5, 4)  # bulk discount 5%
        assert self.cart.subtotal() == 9.5
        self.cart.remove_item("milk", 1)
        assert self.cart.items() == {"milk": 3}
        assert self.cart.subtotal() == 7.5

    def test_remove_more_than_present(self):
        self.cart.add_item("bread", 1.0, 2)
        self.cart.remove_item("bread", 3)
        assert "bread" not in self.cart.items()
        assert self.cart.subtotal() == 0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist", 1)

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("itemA", 20.0, 6)  # no bulk discount
        assert self.cart.subtotal() == 120.0
        total = self.cart.total(member=True, coupon="SAVE10")
        expected_total = round(108.0 + 30, 2)
        assert total == expected_total

    def test_invalid_coupon_raises(self):
        self.cart.add_item("foo", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_shipping_free_above_threshold(self):
        self.cart.add_item("expensive", 2000.0, 1)
        total = self.cart.total()
        assert cart.shipping_fee(2000.0) == 0
        assert total == 2000.0
