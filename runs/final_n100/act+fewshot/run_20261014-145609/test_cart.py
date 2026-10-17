import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50.5, 20, 40.4),  # 50.5 * 0.8 = 40.4
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# error cases for apply_discount
@pytest.mark.parametrize(
    "price, percent",
    [(-10, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.7],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",      # N must be >=1
        "SAVE51",     # >50
        "DISCOUNT10",
        "SAVEXY",
        "   ",
    ],
)
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_items_and_subtotal(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_add_item_increments_quantity(self):
        self.cart.add_item("apple", 2.5, quantity=3)
        self.cart.add_item("apple", 2.5, quantity=2)
        assert self.cart.items() == {"apple": 5}
        assert self.cart.subtotal() == 12.5

    def test_add_different_items(self):
        self.cart.add_item("apple", 1.0, quantity=2)
        self.cart.add_item("banana", 0.5, quantity=4)
        assert self.cart.items() == {"apple": 2, "banana": 4}

    def test_remove_item_decrements_quantity(self):
        self.cart.add_item("orange", 1.5, quantity=5)
        self.cart.remove_item("orange", quantity=3)
        assert self.cart.items() == {"orange": 2}
        assert self.cart.subtotal() == 3.0

    def test_remove_more_than_present_removes_all(self):
        self.cart.add_item("pear", 1.2, quantity=2)
        self.cart.remove_item("pear", quantity=5)
        assert self.cart.items() == {}

    def test_total_with_member_and_coupon(self):
        # Cart: 3 apples @ $10 => $30, shipping fee 0 (subtotal >=1000?) no, subtotal 30
        self.cart.add_item("item", 10, quantity=3)  # subtotal 30
        # Member pays half shipping (30), apply coupon SAVE20 -> 20% discount on subtotal
        total = self.cart.total(member=True, coupon="SAVE20")
        # subtotal after coupon: 30 * 0.8 = 24
        # shipping fee for subtotal 30 is 60; member gets 30
        # final total: 24 + 30 = 54
        assert total == 54.0

    def test_total_without_member_or_coupon(self):
        self.cart.add_item("widget", 5, quantity=2)  # subtotal 10
        total = self.cart.total()
        # shipping fee 60, no member, no coupon
        assert total == 70.0

    def test_total_with_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_shipping_free_on_threshold(self):
        # subtotal exactly 1000, shipping free
        self.cart.add_item("expensive", 200, quantity=5)  # 200*5 = 1000
        assert self.cart.subtotal() == 1000.0
        total = self.cart.total()
        # no shipping fee
        assert total == 1000.0
