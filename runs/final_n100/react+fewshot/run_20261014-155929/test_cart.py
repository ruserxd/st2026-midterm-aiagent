import pytest
import cart

# ----- apply_discount -----
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (123.456, 20, 98.7648),    # check rounding to 2 decimals
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == round(expected, 2)

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),      # below 10
        (9, 0),      # just below 10
        (10, 5),     # boundary 10
        (49, 5),     # just below 50
        (50, 10),    # boundary 50
        (99, 10),    # just below 100
        (100, 15),   # boundary 100
        (150, 15),   # above 100
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 1.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    " SAVE30 ": 30,
    "sAvE50": 50,
}

@pytest.mark.parametrize("code, expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVE51", "DISCOUNT10", "SAVExx", ""]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),      # below 1000
        (999.99, True, 30),  # member gets half
        (500, False, 60),
        (1000, False, 0),     # free shipping
        (1500, True, 0),      # also free for members
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # items should start empty
    def test_initial_items_empty(self):
        assert self.cart.items() == {}

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1.5, 2)
        self.cart.add_item("banana", 1.5, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_conflicting_price_raises(self):
        self.cart.add_item("orange", 3.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4.0, 1)

    def test_remove_item_partial(self):
        self.cart.add_item("carrot", 0.5, 5)
        self.cart.remove_item("carrot", 2)
        assert self.cart.items() == {"carrot": 3}

    def test_remove_item_complete(self):
        self.cart.add_item("date", 1.0, 2)
        self.cart.remove_item("date", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("fig", 1)

    # subtotal calculation with bulk discounts
    def test_subtotal_no_discount(self):
        self.cart.add_item("gadget", 10.0, 4)   # <10 -> no discount
        assert self.cart.subtotal() == 40.00

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("widget", 5.0, 12)   # >=10 -> 5% discount
        expected = round(5.0 * 12 * 0.95, 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_multiple_items(self):
        self.cart.add_item("itemA", 3.0, 6)     # <10 -> no discount
        self.cart.add_item("itemB", 4.0, 55)    # >=50 -> 10% discount
        total_a = 3.0 * 6
        total_b = round(4.0 * 55 * 0.90, 2)
        assert self.cart.subtotal() == round(total_a + total_b, 2)

    def test_total_no_coupon_member(self):
        self.cart.add_item("thing", 20.0, 1)     # subtotal 20
        result = self.cart.total(member=True)   # no coupon, member shipping
        # 20 -> after coupon none; shipping 30 (member half)
        assert result == round(20 + 30, 2)

    def test_total_with_coupon(self):
        self.cart.add_item("product", 50.0, 1)   # subtotal 50
        # coupon SAVE10 -> 10% off
        after_coupon = 45.0
        shipping = 60 if not False else 30  # member=False default
        expected = round(after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 30.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_zero_cost(self):
        assert self.cart.total() == 0.00
