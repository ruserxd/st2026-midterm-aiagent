import pytest
import cart

# --- apply_discount ---
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),    # no discount
        (50, 100, 0.0),     # full discount
        (99.999, 10, 90.0)  # rounding check
    ]
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)]
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15)
    ]
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5]
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ---
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("sAvE1", 1),
        ("savExx", None)  # invalid, will raise
    ]
)
def test_parse_coupon_valid_and_invalid(code, expected):
    if expected is None:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)
    else:
        assert cart.parse_coupon(code) == expected

# --- shipping_fee ---
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (999.99, False, 60)
    ]
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100]
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart tests ---
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    # items dict
    def test_items_initial_empty(self):
        assert self.c.items() == {}

    def test_add_item_new_and_existing(self):
        self.c.add_item("apple", 2.0, 3)
        assert self.c.items() == {"apple": 3}
        # add more of same item with same price
        self.c.add_item("apple", 2.0, 2)
        assert self.c.items() == {"apple": 5}
        # adding different price raises ValueError
        with pytest.raises(ValueError):
            self.c.add_item("apple", 3.0, 1)

    def test_add_item_invalid_args(self):
        with pytest.raises(ValueError):
            self.c.add_item("pear", -5, 1)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 5, 0)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 5, 2.5)

    def test_remove_item(self):
        self.c.add_item("banana", 1.0, 5)
        self.c.remove_item("banana", 3)
        assert self.c.items() == {"banana": 2}
        # remove remaining
        self.c.remove_item("banana", 2)
        assert self.c.items() == {}
        # removing non‑existent item raises KeyError
        with pytest.raises(KeyError):
            self.c.remove_item("orange", 1)

    def test_subtotal(self):
        # no bulk discount for 3 units of 10.0 each
        self.c.add_item("itemA", 10.0, 3)
        assert self.c.subtotal() == 30.00
        # apply bulk discount: 10 units -> 5% off per unit
        self.c = cart.Cart()
        self.c.add_item("itemB", 20.0, 10)
        # 5% of 200 = 10 -> subtotal should be 190.00
        assert self.c.subtotal() == 190.00
        # test rounding: price not cleanly divisible by discount percent
        self.c = cart.Cart()
        self.c.add_item("itemC", 99.999, 10)  # 5% off of 999.99 -> 950.0
        assert self.c.subtotal() == 950.00

    def test_total_no_coupon_member(self):
        # subtotal < 1000, member pays half shipping
        self.c.add_item("x", 500, 2)  # subtotal 1000 => free shipping
        assert self.c.total(member=True) == 1000.00
        # if subtotal just below 1000
        self.c = cart.Cart()
        self.c.add_item("y", 499, 1)
        expected = round(499 + 60, 2)
        assert self.c.total() == expected

    def test_total_with_coupon_and_invalid(self):
        self.c.add_item("z", 200, 5)  # subtotal 1000 -> free shipping
        with pytest.raises(ValueError):
            self.c.total(coupon="invalid")
        # valid coupon
        total = self.c.total(coupon="SAVE10")
        # subtotal 1000, after 10% off => 900, no shipping
        assert total == 900.00

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0

    def test_total_rounding(self):
        # create scenario where rounding matters
        self.c.add_item("w", 33.333, 3)  # 99.999 -> 5% off => 94.9995 -> rounded to 95.00
        subtotal = round(33.333 * 3 * (1 - 0.05), 2)
        shipping = cart.shipping_fee(subtotal)
        total_expected = round(subtotal + shipping, 2)
        assert self.c.total() == total_expected
