import pytest
import cart

def round_2(x):
    """Round a numeric value to two decimal places using Python's round."""
    return round(x, 2)

# -----------------------------------------------------------------------------
# apply_discount tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),          # Example from spec
        (100.0, 0, 100.0),           # No discount
        (100.0, 100, 0.0),           # Full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [
        (-1.0, 10),   # negative price
        (50.0, -5),   # negative percent
        (30.0, 105),  # percent > 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# -----------------------------------------------------------------------------
# bulk_discount_percent tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),      # <10 -> no discount
        (10, 5),     # >=10 but <50 -> 5%
        (49, 5),     # just below 50
        (50, 10),    # >=50 but <100 -> 10%
        (99, 10),    # just below 100
        (100, 15),   # >=100 -> 15%
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, -5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# -----------------------------------------------------------------------------
# parse_coupon tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SAVE30  ", 30),
        ("SAVE50", 50)
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "",            # empty string
        "SAVE",         # no number
        "SA V E10",     # space inside
        "save0",        # out of range (1-50)
        "save51",       # >50
        "DISCOUNT10"    # wrong prefix
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# -----------------------------------------------------------------------------
# shipping_fee tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0.0, False, 60),   # below threshold
        (999.99, True, 30),  # member pays half
        (1000.0, False, 0),  # free shipping
        (2000.0, True, 0),   # always free when subtotal >= 1000
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10.0, -1.0])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Additional test for exact threshold with member=True
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000.0, True, 0),
    ],
)
def test_shipping_fee_threshold(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# -----------------------------------------------------------------------------
# Cart class tests
# -----------------------------------------------------------------------------

class TestCart:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.cart = cart.Cart()

    def test_initial_empty_items(self):
        assert self.cart.items() == {}

    # ------------------------ add_item tests ------------------------
    def test_add_item_basic(self):
        self.cart.add_item("apple", 0.5, quantity=3)
        assert self.cart.items() == {"apple": 3}
        # Adding same item increases quantity
        self.cart.add_item("apple", 0.5, quantity=2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_mismatched_price(self):
        self.cart.add_item("banana", 1.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.5, quantity=1)

    def test_add_item_invalid_unit_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -0.1, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 0.5, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 0.5, quantity=-2)

    # ------------------------ remove_item tests ------------------------
    def test_remove_item_partial_and_full(self):
        self.cart.add_item("orange", 0.8, quantity=5)
        # Remove 3 - remaining 2
        self.cart.remove_item("orange", quantity=3)
        assert self.cart.items() == {"orange": 2}
        # Remove the last two units
        self.cart.remove_item("orange", quantity=2)
        assert self.cart.items() == {}

    def test_remove_item_more_than_present(self):
        self.cart.add_item("grape", 0.2, quantity=3)
        # Removing more than present should remove the item entirely
        self.cart.remove_item("grape", quantity=5)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    # ------------------------ items method tests ------------------------
    def test_items_returns_copy(self):
        self.cart.add_item("kiwi", 0.7, quantity=4)
        d = self.cart.items()
        d["kiwi"] = 10  # modify returned dict
        # The cart's internal should remain unchanged
        assert self.cart.items() == {"kiwi": 4}

    # ------------------------ subtotal tests ------------------------
    def test_subtotal_no_discount(self):
        self.cart.add_item("mango", 20.0, quantity=3)  # qty<10 - no discount
        assert round_2(self.cart.subtotal()) == 60.0

    def test_subtotal_with_discount(self):
        self.cart.add_item("pineapple", 100.0, quantity=10)  # qty=10 ->5% disc
        expected = round_2(100.0 * 10 * (1 - 0.05))
        assert round_2(self.cart.subtotal()) == expected

    def test_subtotal_multiple_items(self):
        self.cart.add_item("melon", 30.0, quantity=4)     # no discount
        self.cart.add_item("banana", 200.0, quantity=50)   # qty>=50 ->10% disc
        melon = 30.0 * 4
        banana_contrib = round_2(200.0 * 50 * (1 - 0.10))
        expected_total = round_2(melon + banana_contrib)
        assert round_2(self.cart.subtotal()) == expected_total

    def test_subtotal_empty_cart(self):
        assert round_2(self.cart.subtotal()) == 0.0

    # ------------------------ total tests ------------------------
    def test_total_no_coupon_member_and_shipping(self):
        self.cart.add_item("item1", 50.0, quantity=4)  # subtotal 200 <1000 -> shipping 60
        expected = round_2(200 + 60)
        assert round_2(self.cart.total()) == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item1", 50.0, quantity=4)  # subtotal 200
        # apply coupon SAVE10 -> 10% off => discounted = 180
        expected_after_discount = round_2(200 * (1 - 0.10))
        shipping = 30  # member half of 60
        expected_total = round_2(expected_after_discount + shipping)
        assert round_2(self.cart.total(member=True, coupon="SAVE10")) == expected_total

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("item1", 50.0, quantity=4)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart(self):
        assert round_2(self.cart.total()) == 0.0
        # Also check that member flag or coupon doesn't affect empty cart
        assert round_2(self.cart.total(member=True)) == 0.0
        assert round_2(self.cart.total(coupon="SAVE10")) == 0.0

    def test_total_rounding_behavior(self):
        self.cart.add_item("tiny", 99.99, quantity=1)  # subtotal 99.99
        # apply coupon SAVE10 -> discounted = 89.991 rounded to 90.0?
        expected_after_discount = round_2(99.99 * (1 - 0.10))
        shipping = 60  # non-member
        expected_total = round_2(expected_after_discount + shipping)
        assert round_2(self.cart.total()) == expected_total

    def test_total_shipping_after_discount_threshold(self):
        self.cart.add_item("expensive", 300.0, quantity=4)  # subtotal 1200 >1000
        # no coupon -> shipping free
        assert round_2(self.cart.total()) == 1200.0

        # with coupon SAVE50 -> discounted = 600 -> shipping 60
        expected_after_discount = round_2(1200 * (1 - 0.5))
        shipping_fee = 60  # non-member
        expected_total = round_2(expected_after_discount + shipping_fee)
        assert round_2(self.cart.total(coupon="SAVE50")) == expected_total
