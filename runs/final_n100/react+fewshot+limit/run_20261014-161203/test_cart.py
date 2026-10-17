import pytest
import cart


def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # round to two decimals
    assert cart.apply_discount(123.456, 10) == round(123.456 * 0.9, 2)


@pytest.mark.parametrize(
    "price,percent",
    [
        (-1, 10),          # negative price
        (100, -5),         # percent below 0
        (100, 105),        # percent above 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
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
    [-1, 0, 3.5],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)


def test_parse_coupon_valid():
    # Case-insensitive and whitespace tolerant
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30  ") == 30


@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # below min
        "SAVE51",         # above max
        "SAV10",          # wrong prefix
        "ABC123",         # random
        "",               # empty string
        "   ",            # only whitespace
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (999.99, True, 30),
        (500, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected


@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------------------------------------------------------------------------- #
# Cart class tests
# --------------------------------------------------------------------------- #

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 5.0, 3)
        assert self.cart.items() == {"apple": 3}
        # unit price unchanged when adding same item
        self.cart.add_item("apple", 5.0, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):          # negative price
            self.cart.add_item("banana", -1, 1)
        with pytest.raises(ValueError):          # non-positive quantity
            self.cart.add_item("banana", 2, 0)
        with pytest.raises(ValueError):          # wrong unit price for existing item
            self.cart.add_item("apple", 5.0, 1)   # set up first
            self.cart.add_item("apple", 6.0, 1)

    def test_remove_item(self):
        self.cart.add_item("orange", 3.0, 4)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": 2}
        # remove all remaining
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_and_total(self):
        self.cart.add_item("pen", 1.5, 2)          # $3
        self.cart.add_item("notebook", 5.0, 1)     # $5
        subtotal = cart.apply_discount(8.0, 0)      # no discount
        assert self.cart.subtotal() == 8.0

        total = self.cart.total()
        assert total == round(subtotal + cart.shipping_fee(subtotal), 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("tshirt", 20.0, 10)      # $200
        subtotal = 200.0
        discount = cart.parse_coupon("SAVE10")
        total = self.cart.total(member=True, coupon="SAVE10")
        expected_subtotal = round(subtotal * (1 - discount / 100), 2)
        shipping = cart.shipping_fee(expected_subtotal, member=True)
        assert total == round(expected_subtotal + shipping, 2)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
