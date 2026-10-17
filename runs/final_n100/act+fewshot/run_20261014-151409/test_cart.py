import pytest
import cart

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (55, 10),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -3, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEXX", "SAVE0", "SAVE51", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (1200, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart behavior basics
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.5, 3)
        items = self.cart.items()
        assert len(items) == 1
        name, unit_price, quantity = items[0]
        assert name == "apple"
        assert unit_price == 1.5
        assert quantity == 3

    def test_remove_item(self):
        self.cart.add_item("banana", 0.75, 5)
        self.cart.remove_item("banana", 2)
        items = self.cart.items()
        assert len(items) == 1
        name, unit_price, quantity = items[0]
        assert name == "banana"
        assert unit_price == 0.75
        assert quantity == 3

    def test_subtotal(self):
        self.cart.add_item("item1", 10, 2)
        self.cart.add_item("item2", 5, 4)
        assert self.cart.subtotal() == 20 + 20

    def test_total_no_coupon_member_false(self):
        self.cart.add_item("product", 200, 1)
        # subtotal 200; shipping non-member 60 => total 260.0
        assert self.cart.total(member=False) == 260.0

    def test_total_with_coupon_and_member_true(self):
        self.cart.add_item("widget", 100, 2)  # subtotal 200
        # coupon SAVE10 reduces by 10% => 180
        # member shipping half of 60 =30 -> total 210.0
        assert self.cart.total(member=True, coupon="SAVE10") == 210.0

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
