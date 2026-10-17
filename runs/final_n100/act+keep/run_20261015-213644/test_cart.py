import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ------------------
# Utility helper
# ------------------
def round2(x):
    return round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        (" SAVE5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVExx", " "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1500.5, True, 0),
        (999.99, False, 60),
        (999.99, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class behaviour ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    # add_item
    def test_add_new_item(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple": 3}

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 2.5, quantity=2)
        self.cart.add_item("banana", 2.5, quantity=1)
        assert self.cart.items() == {"banana": 3}

    def test_add_existing_diff_price_raises(self):
        self.cart.add_item("pear", 0.9)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0)

    @pytest.mark.parametrize("unit_price,quantity", [(-1, 5), (1, 0), (2.5, -3)])
    def test_add_invalid(self, unit_price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", unit_price, quantity)

    # remove_item
    def test_remove_partial(self):
        self.cart.add_item("mango", 3.0, quantity=5)
        self.cart.remove_item("mango", quantity=2)
        assert self.cart.items() == {"mango": 3}

    def test_remove_all_removes(self):
        self.cart.add_item("peach", 4.0, quantity=2)
        self.cart.remove_item("peach")  # default qty 1 - remaining 1
        assert self.cart.items() == {"peach": 1}
        self.cart.remove_item("peach")
        assert self.cart.items() == {}

    def test_remove_more_than_present(self):
        self.cart.add_item("grape", 0.5, quantity=2)
        self.cart.remove_item("grape", quantity=3)  # should remove fully
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    # subtotal and discounts
    def test_subtotal_without_discount(self):
        self.cart.add_item("item", 10.0, quantity=9)
        assert round2(self.cart.subtotal()) == 90.0  # no bulk discount

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("widget", 5.0, quantity=12)  # 5% off
        expected = 5.0 * 12 * (1 - 0.05)
        assert round2(self.cart.subtotal()) == round2(expected)

    def test_subtotal_multiple_items(self):
        self.cart.add_item("small", 1.0, quantity=9)   # no discount
        self.cart.add_item("large", 10.0, quantity=50)  # 10% off
        small = 1.0 * 9
        large = 10.0 * 50 * (1 - 0.10)
        assert round2(self.cart.subtotal()) == round2(small + large)

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("book", 20.0, quantity=1)
        subtotal = 20.0
        shipping = shipping_fee(subtotal)
        assert round2(self.cart.total()) == round2(subtotal + shipping)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("pen", 5.0, quantity=50)  # 10% bulk discount
        subtotal = 5.0 * 50 * (1 - 0.10)
        coupon_discount = parse_coupon("SAVE20") / 100
        after_coupon = subtotal * (1 - coupon_discount)
        shipping = shipping_fee(after_coupon, member=True)
        total_expected = round2(after_coupon + shipping)
        assert self.cart.total(member=True, coupon="SAVE20") == total_expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("notebook", 3.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_zero_no_shipping(self):
        assert self.cart.total() == 0
