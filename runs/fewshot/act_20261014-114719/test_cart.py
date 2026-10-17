import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Boundary and error cases
def test_apply_discount_negative_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

def test_apply_discount_invalid_percent():
    for p in (-5, 105):
        with pytest.raises(ValueError):
            cart.apply_discount(100, p)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,percent", [
    (5, 0),
    (10, 5),
    (20, 5),
    (50, 10),
    (75, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# Error cases
def test_bulk_discount_percent_nonpositive():
    for q in (0, -1, 3.5):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(q)

# Tests for parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("sAve50", 50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# Invalid coupons
@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "INVALID",
    "SAVE-5",
    "SAVEX",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# Error case
def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": (1.0, 3)}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.5, 2)
        self.cart.add_item("banana", 0.5, 4)
        assert self.cart.items() == {"banana": (0.5, 6)}

    def test_add_item_existing_diff_price(self):
        self.cart.add_item("pear", 1.2, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.3, 2)

    def test_remove_item_partial(self):
        self.cart.add_item("orange", 0.8, 5)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": (0.8, 3)}

    def test_remove_item_all(self):
        self.cart.add_item("grape", 0.9, 4)
        self.cart.remove_item("grape", 4)
        assert "grape" not in self.cart.items()

    def test_subtotal_and_total(self):
        self.cart.add_item("book", 10, 2)   # $20
        self.cart.add_item("pen", 1.5, 3)   # $4.5
        assert self.cart.subtotal() == 24.5
        # no discount, non-member
        assert self.cart.total(member=False) == 24.5 + cart.shipping_fee(24.5)
        # member with coupon SAVE10
        assert self.cart.total(member=True, coupon="SAVE10")

    def test_total_bulk_and_shipping(self):
        # buy 120 of item to get bulk discount
        self.cart.add_item("widget", 2, 120)  # $240 before bulk
        subtotal = 240
        expected_subtotal = subtotal * (1 - cart.bulk_discount_percent(120)/100)
        assert abs(self.cart.subtotal() - 240) < 1e-6
        total_no_coupon = expected_subtotal + cart.shipping_fee(expected_subtotal)
        assert abs(self.cart.total(member=False) - total_no_coupon) < 1e-6
