import pytest
import cart

# ------------------- apply_discount --------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (30, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------- bulk_discount_percent --------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.7],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------- parse_coupon --------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEE10", "  ", "SAVE-5"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------- shipping_fee --------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------- Cart class --------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 2.5)
        assert self.cart.items() == {"apple": 3, "banana": 1}

    def test_add_existing_increases_quantity_and_raises_on_price_mismatch(self):
        self.cart.add_item("pear", 3.0, 2)
        # same price -> quantity increases
        self.cart.add_item("pear", 3.0, 1)
        assert self.cart.items() == {"pear": 3}
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 4.0, 1)

    def test_remove_decreases_quantity_and_removes_when_zero(self):
        self.cart.add_item("orange", 2.0, 5)
        self.cart.remove_item("orange", 3)
        assert self.cart.items() == {"orange": 2}
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises_keyerror(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_with_bulk_discount(self):
        # 10 units of item A, unit price $10 -> bulk discount 5%
        self.cart.add_item("itemA", 10.0, 10)
        expected = round(10 * 10 * (1 - 0.05), 2)  # 95
        assert self.cart.subtotal() == expected

    def test_subtotal_empty_cart(self):
        assert self.cart.subtotal() == 0

    def test_total_without_coupon_and_member(self):
        self.cart.add_item("item", 100.0, 1)
        subtotal = self.cart.subtotal()
        shipping = cart.shipping_fee(subtotal, False)
        expected = round(subtotal + shipping, 2)
        assert self.cart.total() == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 200.0, 1)
        subtotal = self.cart.subtotal()
        # coupon SAVE20 => 20% discount
        after_discount = round(subtotal * (1 - 0.20), 2)
        shipping = cart.shipping_fee(after_discount, True)
        expected = round(after_discount + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", 50.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0
