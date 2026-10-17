import pytest
import cart

# --------- apply_discount ---------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 10, 111.11),  # 123.45 * 0.9 = 111.105 -> round to 2 decimals
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --------- bulk_discount_percent ---------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),  # corrected expectation per spec
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# --------- parse_coupon ---------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30 ", 30),
        ("SAVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "NOTACODE", "SAVE-5", "SA V10", "  SAVE ", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------- shipping_fee ---------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100.5],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------- Cart class ---------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 2}
        # add same item with same price
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -0.5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, 0)
        # different price for same name
        self.cart.add_item("pear", 2.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 3.0, 1)

    def test_remove_item(self):
        self.cart.add_item("milk", 2.0, 5)
        self.cart.remove_item("milk", 2)
        assert self.cart.items() == {"milk": 3}
        # remove remaining
        self.cart.remove_item("milk", 3)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_subtotal_bulk_discount(self):
        # 10 apples at $2 each = bulk discount 5%
        self.cart.add_item("apple", 2.0, 10)
        expected = round(2.0 * 10 * (1 - 0.05), 2)  # 19.0
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_or_member(self):
        self.cart.add_item("item", 50, 2)
        subtotal = 100.0
        shipping = cart.shipping_fee(subtotal)
        total_expected = round(subtotal + shipping, 2)
        assert self.cart.total() == total_expected

    def test_total_with_coupon(self):
        self.cart.add_item("item", 200, 1)
        subtotal = 200.0
        after_discount = cart.apply_discount(subtotal, 10)  # 180
        shipping = cart.shipping_fee(after_discount)
        total_expected = round(after_discount + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_with_member(self):
        self.cart.add_item("item", 200, 1)
        subtotal = 200.0
        after_discount = subtotal  # no coupon
        shipping = cart.shipping_fee(after_discount, member=True)  # 30
        total_expected = round(subtotal + shipping, 2)
        assert self.cart.total(member=True) == total_expected

    def test_total_with_invalid_coupon_raises(self):
        self.cart.add_item("item", 50, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BAD")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
