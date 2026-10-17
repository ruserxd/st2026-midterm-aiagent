import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (99.999, 10, 90.0),        # rounding to 2 decimals
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid inputs for price and percent
@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),      # below 10
        (10, 5),     # threshold 10
        (49, 5),     # between 10 and 50
        (50, 10),    # threshold 50
        (99, 10),    # between 50 and 100
        (100, 15),   # threshold 100
        (150, 15),   # above 100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),            # case-insensitive
        ("   SAVE5  ", 5),          # whitespace ignored
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
@pytest.mark.parametrize(
    "code",
    [
        "",                # empty string
        "SAVE0",           # below 1
        "SAVE51",          # above 50
        "SAVEB5",          # bad prefix
        "10SAVE",          # wrong format
        " SAVE-5 ",        # negative number
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),      # free shipping
        (2000, True, 0),       # also free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        # Add items and check internal representation via items()
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 0.5, 2)
        assert self.cart.items() == {"apple": 3, "banana": 2}

    def test_add_existing_increases_quantity_and_price_match(self):
        self.cart.add_item("orange", 0.8, 1)
        # same price increases quantity
        self.cart.add_item("orange", 0.8, 4)
        assert self.cart.items() == {"orange": 5}

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("pear", 0.6, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 0.7, 1)

    def test_remove_item(self):
        self.cart.add_item("milk", 2.5, 4)
        self.cart.remove_item("milk", 3)  # leave 1
        assert self.cart.items() == {"milk": 1}
        self.cart.remove_item("milk", 1)  # remove completely
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_with_bulk_discount_and_rounding(self):
        # 10 apples at $1.00 each => bulk discount 5%
        self.cart.add_item("apple", 1.0, 10)
        expected = round(1.0 * 10 * (1 - cart.bulk_discount_percent(10)/100), 2)  # 9.5
        assert self.cart.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("book", 30, 2)   # $60 subtotal
        total = self.cart.total(coupon="SAVE10")
        # 10% coupon => 54; shipping fee for non-member: 60 -> total 114
        assert total == 114.0

    def test_total_member_no_coupon(self):
        self.cart.add_item("pen", 5, 1)      # $5 subtotal
        total = self.cart.total(member=True)
        # shipping fee for member: 30 -> total 35
        assert total == 35.0

    def test_total_free_shipping_after_coupon(self):
        # Subtotal $1000 => free shipping; apply coupon to see if it still free
        self.cart.add_item("expensive", 500, 2)  # $1000 subtotal
        total = self.cart.total(coupon="SAVE50")  # 50% off -> $500
        assert cart.shipping_fee(500, member=False) == 60  # shipping on discounted amount
        assert total == round(500 + 60, 2)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0

# ---------- Edge Cases and Error Propagation ----------
@pytest.mark.parametrize(
    "items",
    [
        ([("item1", -1, 1)], ValueError),          # negative unit price
        ([("item2", 10, 0)], ValueError),           # non-positive quantity
        ([("item3", 5, 1.5)], ValueError),         # fractional quantity
    ],
)
def test_add_item_invalid(items):
    c = cart.Cart()
    for name, price, qty in items[0]:
        with pytest.raises(ValueError if isinstance(items[1], type) else AssertionError):
            c.add_item(name, price, qty)

# Ensure that invalid coupon passed to total raises ValueError
def test_total_invalid_coupon():
    self_cart = cart.Cart()
    self_cart.add_item("toy", 20, 1)
    with pytest.raises(ValueError):
        self_cart.total(coupon="INVALID")
