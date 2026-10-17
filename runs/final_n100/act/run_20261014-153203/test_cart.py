import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------
# apply_discount tests
# ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected)

# boundary conditions for price and percent
@pytest.mark.parametrize(
    "price",
    [-1, -100],
)
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-1, 101, 150],
)
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ----------
# bulk_discount_percent tests
# ----------
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
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.7],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----------
# parse_coupon tests
# ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAV10",   # missing 'E'
        "SAVE0",   # below 1
        "SAVE51",  # above 50
        "XYZ20",   # wrong prefix
        " SAVE-5 ",# negative number
        "" ,
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----------
# shipping_fee tests
# ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----------
# Cart class tests
# ----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        assert self.cart.items() == {}
        self.cart.add_item("apple", 1.5, 2)
        self.assert_items({"apple": 2})
        self.cart.add_item("banana", 0.5, 3)
        self.assert_items({"apple": 2, "banana": 3})

    def assert_items(self, expected):
        assert self.cart.items() == expected

    def test_add_same_item_increase_quantity(self):
        self.cart.add_item("orange", 0.8, 1)
        self.cart.add_item("orange", 0.8, 4)
        assert self.cart.items() == {"orange": 5}

    def test_add_different_price_raises(self):
        self.cart.add_item("pear", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.2, 1)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("mango", 2.0, 5)
        self.cart.remove_item("mango", 3)
        assert self.cart.items() == {"mango": 2}
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("peach", 1)

    def test_subtotal_and_total_no_discount(self):
        self.cart.add_item("itemA", 10, 2)   # 20
        self.cart.add_item("itemB", 5, 3)    # 15
        assert self.cart.subtotal() == 35
        assert self.cart.total() == pytest.approx(35 + shipping_fee(35))

    def test_total_with_bulk_discount(self):
        # bulk discount applies to each item separately
        self.cart.add_item("bulk", 1, 100)   # subtotal 100, bulk percent 15%
        expected_subtotal = 100
        discounted = apply_discount(expected_subtotal, 15)
        assert self.cart.total() == pytest.approx(discounted + shipping_fee(discounted))

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("itemC", 200, 1)   # subtotal 200
        total = self.cart.total(member=True, coupon="SAVE10")
        discounted = apply_discount(200, 10)
        expected = discounted + shipping_fee(discounted, member=True)
        assert total == pytest.approx(expected)
