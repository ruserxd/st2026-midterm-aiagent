import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid values
@pytest.mark.parametrize("price", [-1, -0.01])
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
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 1.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SAVE5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
@pytest.mark.parametrize("code", ["SAVE0", "SAVEX", "DISCOUNT10", "SAVE-5", "SAVE101", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests: focus on totals and item existence
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items_count(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 0.5)
        items = self.cart.items()
        assert len(items) == 2
        names = [item["name"] for item in items]
        assert set(names) == {"apple", "banana"}

    def test_remove_partial(self):
        self.cart.add_item("orange", 0.8, 5)
        self.cart.remove_item("orange", 2)
        remaining = next((i for i in self.cart.items() if i["name"] == "orange"), None)
        assert remaining is not None and remaining["quantity"] == 3

    def test_remove_more_than_exists(self):
        self.cart.add_item("grape", 0.2, 4)
        self.cart.remove_item("grape", 10)
        # item should be removed completely
        assert all(i["name"] != "grape" for i in self.cart.items())

    def test_subtotal(self):
        self.cart.add_item("milk", 3.0, 2)   # 6
        self.cart.add_item("bread", 2.5, 1)  # 8.5
        assert self.cart.subtotal() == pytest.approx(8.5)

    def test_total_without_member_or_coupon(self):
        self.setup_method(None)
        self.cart.add_item("milk", 3.0, 2)
        self.cart.add_item("bread", 2.5, 1)
        assert self.cart.total() == pytest.approx(8.5 + cart.shipping_fee(8.5))

    def test_total_with_member(self):
        self.setup_method(None)
        self.cart.add_item("milk", 3.0, 2)
        self.cart.add_item("bread", 2.5, 1)
        discounted = cart.apply_discount(8.5, 30)
        expected = discounted + cart.shipping_fee(discounted, member=True)
        assert self.cart.total(member=True) == pytest.approx(expected)

    def test_total_with_coupon(self):
        self.setup_method(None)
        self.cart.add_item("milk", 3.0, 2)
        self.cart.add_item("bread", 2.5, 1)
        discounted = cart.apply_discount(8.5, 10)
        expected = discounted + cart.shipping_fee(discounted)
        assert self.cart.total(coupon="SAVE10") == pytest.approx(expected)
