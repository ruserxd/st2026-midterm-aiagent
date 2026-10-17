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

# errors for apply_discount
@pytest.mark.parametrize("price,percent", [(-1,10),(50,-5),(50,105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),  # spec says >=50 ->10
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# errors for bulk_discount_percent
@pytest.mark.parametrize("qty", [0,-5,1.5])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon valid cases
@pytest.mark.parametrize("code,percent", [
    ("SAVE10",10),
    ("save20",20),  # case-insensitive should pass
    (" SAVE30 ",30),
])
def test_parse_coupon(code, percent):
    assert cart.parse_coupon(code) == percent

# parse_coupon error cases for case sensitivity bug
@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", " 10SAVE", ""])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (1000, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# errors for shipping_fee
@pytest.mark.parametrize("subtotal", [-1,-0.01])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 2.0, 3)
        self.cart.add_item("banana", 1.5)
        assert self.cart.items() == {"apple":3, "banana":1}

    def test_add_existing_same_price(self):
        self.cart.add_item("apple", 2.0, 2)
        self.cart.add_item("apple", 2.0, 1)
        assert self.cart.items() == {"apple":3}

    def test_add_existing_different_price_error(self):
        self.cart.add_item("apple", 2.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 3.0, 1)

    def test_remove_item(self):
        self.cart.add_item("orange", 1.0, 5)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange":3}

    def test_remove_all_removes_item(self):
        self.cart.add_item("pear", 2.5, 2)
        self.cart.remove_item("pear", 2)
        # spec: item removed when quantity reaches 0
        assert self.cart.items() == {}

    def test_remove_more_than_present(self):
        self.cart.add_item("grape", 0.5, 1)
        self.cart.remove_item("grape", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_key_error(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango")

    def test_subtotal_simple_no_discount(self):
        self.cart.add_item("item", 10.0, 2)
        assert self.cart.subtotal() == 20.0

    def test_subtotal_with_bulk_discount(self):
        # 10 units gets 5% discount
        self.cart.add_item("bulk", 100.0, 10)
        expected = 100.0 * 10 * 0.95
        assert self.cart.subtotal() == round(expected,2)

    def test_total_no_coupon_member(self):
        self.cart.add_item("pencil", 1.0, 3)
        # subtotal 3, no discount, shipping 60 for non-member
        expected = 3 + 60
        assert self.cart.total(member=False) == round(expected,2)

    def test_total_coupon_and_member(self):
        self.cart.add_item("pen", 50.0, 1)
        # subtotal 50, coupon SAVE10 -> 45
        expected = 45 + 30  # member half shipping
        assert self.cart.total(member=True, coupon="SAVE10") == round(expected,2)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
