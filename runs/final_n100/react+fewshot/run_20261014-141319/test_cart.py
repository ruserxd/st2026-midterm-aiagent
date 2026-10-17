import pytest
import cart

# ----- apply_discount tests -----
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),      # example from spec
        (100, 0, 100.0),       # no discount
        (50, 100, 0.0),        # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid inputs for apply_discount
@pytest.mark.parametrize(
    "price, percent",
    [
        (-10, 20),   # negative price
        (100, -5),   # negative percent
        (100, 105),  # percent > 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent tests -----
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),   # below threshold
        (10, 5),  # exactly at first threshold
        (49, 5),  # just before second threshold
        (50, 10), # at second threshold
        (99, 10), # just before third
        (100, 15),# at final threshold
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity for bulk_discount_percent
@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon tests -----
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",       # N < 1
        "SAVE51",      # N > 50
        "save",        # missing number
        "DISCOUNT10",  # wrong prefix
        "SAVEX",       # non‑numeric suffix
        " ",           # empty after strip
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee tests -----
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),      # below threshold, non‑member
        (999.99, False, 60),
        (1000, False, 0),    # free shipping threshold
        (1500, True, 30),    # member discount on fee
    ],
)
def test_shipping_fee_valid(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal for shipping_fee
@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class tests -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}

    # add_item basic functionality
    def test_add_new_item(self):
        self.cart.add_item("apple", 0.5, 3)
        assert self.cart.items() == {"apple": (0.5, 3)}

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 1.2, 2)
        self.cart.add_item("banana", 1.2, 4)
        assert self.cart.items() == {"banana": (1.2, 5)}

    def test_add_existing_diff_price(self):
        self.cart.add_item("orange", 0.8, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.9, 2)

    # remove_item tests
    def test_remove_quantity_reduces(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": (1.5, 2)}

    def test_remove_entire_item(self):
        self.cart.add_item("grape", 2.0, 3)
        self.cart.remove_item("grape", 3)
        assert "grape" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    # subtotal calculation
    def test_subtotal_simple(self):
        self.cart.add_item("kiwi", 1.0, 5)
        assert self.cart.subtotal() == 5.0

    def test_subtotal_multiple_items(self):
        self.cart.add_item("mango", 3.0, 2)
        self.cart.add_item("papaya", 4.0, 1)
        assert self.cart.subtotal() == 10.0

    # total with member and coupon
    def test_total_no_member_coupon(self):
        self.cart.add_item("watermelon", 5.0, 2)   # subtotal = 10
        assert self.total_calc("a") == 10.0

    def test_total_with_member_discount(self:
"""
        """
        self.cart..??\n
