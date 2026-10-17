import pytest
import cart

# helper for rounding tolerance
def close(a, b, eps=1e-9):
    return abs(a - b) < eps

# -------- apply_discount --------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (100, -5), (50, 120)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# -------- bulk_discount_percent --------
@pytest.mark.parametrize(
    "qty,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -3, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# -------- parse_coupon --------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("   SaVe50   ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # below min
        "SAVE51",         # above max
        "SAVEXX",         # non numeric
        "10SAVE",         # wrong format
        "",               # empty
        "   ",           # only whitespace
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# -------- shipping_fee --------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------- Cart class --------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # add_item and items
    def test_add_and_items(self):
        self.cart.add_item("apple", 1.5, quantity=3)
        self.cart.add_item("banana", 2.0)
        assert self.cart.items() == {"apple": 3, "banana": 1}

    # add existing item with same price
    def test_add_existing_same_price(self):
        self.cart.add_item("pen", 0.5, quantity=2)
        self.cart.add_item("pen", 0.5, quantity=3)
        assert self.cart.items()["pen"] == 5

    # add existing item with different price raises ValueError
    def test_add_existing_different_price(self):
        self.cart.add_item("pencil", 0.2)
        with pytest.raises(ValueError):
            self.cart.add_item("pencil", 0.3)

    # remove_item decreases quantity and removes when zero
    def test_remove_item(self):
        self.cart.add_item("notebook", 5.0, quantity=4)
        self.cart.remove_item("notebook", quantity=2)
        assert self.cart.items()["notebook"] == 2
        self.cart.remove_item("notebook", quantity=2)
        assert "notebook" not in self.cart.items()

    # remove non-existent raises KeyError
    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("ghost", 1)

    # subtotal calculation with bulk discounts
    def test_subtotal_bulk_discount(self):
        # 10 apples at $1 each -> 5% discount on the item total
        self.cart.add_item("apple", 1.0, quantity=10)
        expected = round(1.0 * 10 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_multiple_items(self):
        # 3 oranges ($1 each) no discount
        # 50 mangoes ($2 each) -> 10% discount
        self.cart.add_item("orange", 1.0, quantity=3)
        self.cart.add_item("mango", 2.0, quantity=50)
        orange_total = 3 * 1.0
        mango_total = round(50 * 2.0 * (1 - 0.10), 2)
        assert self.cart.subtotal() == round(orange_total + mango_total, 2)

    # total with coupon and shipping
    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("gift", 200.0, quantity=6)  # 5% bulk discount on item
        subtotal = round(200.0 * 6 * (1 - 0.05), 2)
        coupon_percent = cart.parse_coupon("SAVE20")
        after_coupon = round(subtotal * (1 - coupon_percent / 100), 2)
        shipping = cart.shipping_fee(after_coupon, member=False)
        total_expected = round(after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE20") == total_expected

    # total on empty cart is 0 and no shipping
    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
        assert self.cart.total(member=True) == 0.0

    # coupon validation via Cart.total
    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
