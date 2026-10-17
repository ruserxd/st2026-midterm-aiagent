import pytest
import cart

# Helper expectations based on the specification

def _expected_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# apply_discount
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.999, 10, 90.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize(
    "qty,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.5])
def test_bulk_discount_percent_error(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25 ", 25),
        (" SAVE50 ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVEX", "10SAVE", "save51", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 2)
        self.cart.add_item("banana", 0.5, 3)
        expected = {
            "apple": (1.0, 2),
            "banana": (0.5, 3),
        }
        assert self.cart.items() == expected

    def test_add_existing_increases_quantity(self):
        self.cart.add_item("apple", 1.0, 2)
        self.cart.add_item("apple", 1.0, 1)
        assert self.cart.items()["apple"] == (1.0, 3)

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("apple", 1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 1.5, 1)

    def test_remove_decreases_and_removes(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.remove_item("apple", 2)
        assert self.cart.items()["apple"] == (1.0, 1)
        self.cart.remove_item("apple", 1)
        assert "apple" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear")

    def test_subtotal_and_total_member_coupon(self):
        self.cart.add_item("item1", 200, 3)
        self.cart.add_item("item2", 50, 10)
        subtotal = self.cart.subtotal()
        assert subtotal == round(600 + 475.0, 2)
        discounted = _expected_discount(subtotal, 5)
        shipping = cart.shipping_fee(discounted, member=True)
        total_expected = round(discounted + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE5") == total_expected

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.00
