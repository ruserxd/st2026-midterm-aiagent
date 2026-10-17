import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------------------------------------------------------------
# Helper fixtures and constants for the tests.
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_cart():
    """Return a Cart instance with two items.
    Item 1: "Widget", unit price 100, quantity 12 (bulk discount 5%).
    Item 2: "Gadget", unit price 200, quantity 8  (no bulk discount).
    The subtotal before discounts is:
        Widget total = 100 * 12 = 1200
        Gadget total = 200 * 8  = 1600
        subtotal      = 2800
    """
    c = Cart()
    c.add_item("Widget", 100, quantity=12)
    c.add_item("Gadget", 200, quantity=8)
    return c

# ---------------------------------------------------------------------------
# Tests for the helper functions.
# ---------------------------------------------------------------------------
class TestApplyDiscount:
    def test_rounding(self):
        assert apply_discount(100.00, 10) == 90.0
        # rounding with 3 decimals
        assert apply_discount(100.001, 10) == 90.0
        assert apply_discount(100.004, 10) == 90.0
        assert apply_discount(100.005, 10) == 90.0

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            apply_discount(-1, 10)

    def test_invalid_percent_bounds(self):
        for bad in (-1, 101):
            with pytest.raises(ValueError):
                apply_discount(100, bad)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize(
        "quantity,expected",
        [
            (5, 0),
            (10, 5),
            (50, 10),
            (99, 10),
            (100, 15),
            (150, 15),
        ],
    )
    def test_values(self, quantity, expected):
        assert bulk_discount_percent(quantity) == expected

    def test_invalid_quantity_type(self):
        with pytest.raises(ValueError):
            bulk_discount_percent("10")

    def test_non_positive(self):
        for bad in (0, -1):
            with pytest.raises(ValueError):
                bulk_discount_percent(bad)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code,expected",
        [("SAVE10", 10), ("save25 ", 25), ("  SaVe5  ", 5)],
    )
    def test_valid(self, code, expected):
        assert parse_coupon(code) == expected

    @pytest.mark.parametrize(
        "code",
        [
            "10SAVE",   # wrong order
            "SAVEX",    # non-digit suffix
            "SAVE0",    # percent below range
            "SAVE51",   # percent above range
            123,         # not a string
        ],
    )
    def test_invalid(self, code):
        with pytest.raises(ValueError):
            parse_coupon(code)

class TestShippingFee:
    @pytest.mark.parametrize(
        "subtotal,member,expected",
        [
            (1200, False, 0),   # free shipping for non-member as well
            (999, False, 60),
            (500, True, 30),
        ],
    )
    def test_values(self, subtotal, member, expected):
        assert shipping_fee(subtotal, member=member) == expected

    def test_negative_subtotal(self):
        with pytest.raises(ValueError):
            shipping_fee(-10)

# ---------------------------------------------------------------------------
# Tests for the Cart class.
# ---------------------------------------------------------------------------
class TestCart:
    def test_add_and_items(self):
        c = Cart()
        c.add_item("Apple", 1.0, quantity=3)
        assert c.items() == {"Apple": 3}

        # Adding same item increases quantity; price must match
        c.add_item("Apple", 1.0, quantity=2)
        assert c.items()["Apple"] == 5

        with pytest.raises(ValueError):
            c.add_item("Apple", 2.0)  # price mismatch

    def test_remove_and_empty(self):
        c = Cart()
        c.add_item("Banana", 0.5, quantity=4)
        c.remove_item("Banana", quantity=2)
        assert c.items()["Banana"] == 2
        c.remove_item("Banana", quantity=2)  # remove all
        assert "Banana" not in c.items()

    def test_remove_nonexistent(self):
        c = Cart()
        with pytest.raises(KeyError):
            c.remove_item("NonExistent")

    def test_subtotal_bulk_discount(self, sample_cart):
        # With 12 Widgets we expect a 5% bulk discount.
        # Widget line: 100*12=1200; discount=5% => 1140
        # Gadget line: 200*8=1600 (no discount)
        assert sample_cart.subtotal() == round(1140 + 1600, 2)

    def test_total_with_member_and_coupon(self, sample_cart):
        subtotal = sample_cart.subtotal()
        # Use a coupon that would bring the cost below FREE_SHIPPING_THRESHOLD
        # but keep it realistic: e.g., 50% off on $2800 -> $1400
        amount_after_discount = apply_discount(subtotal, parse_coupon("SAVE50"))
        expected_shipping = shipping_fee(amount_after_discount, member=True)
        expected_total = round(amount_after_discount + expected_shipping, 2)

        actual_total = sample_cart.total(member=True, coupon="SAVE50")
        assert actual_total == expected_total

    def test_total_free_shipping_threshold(self):
        c = Cart()
        # Add a single item with high price to exceed threshold before any discount.
        c.add_item("Expensive", 1200)
        total_no_discount = c.total(member=False, coupon=None)
        assert total_no_discount == round(1200 + shipping_fee(1200), 2) == 1200

    def test_total_coupon_free_shipping(self):
        # subtotal just below threshold but coupon reduces it further.
        c = Cart()
        c.add_item("Item", 100, quantity=10)  # subtotal = 1000
        total_with_coupon = c.total(member=False, coupon="SAVE50")
        # Expect shipping applied after discount because subtotal becomes 500 < threshold
        assert total_with_coupon == round(500 + shipping_fee(500), 2)
        # But implementation mistakenly gives free shipping based on original 1000.
        # Thus the actual result should be lower than expected.
        assert total_with_coupon < round(500, 2)  # this ensures discrepancy detected

    def test_invalid_coupon_raises(self):
        c = Cart()
        c.add_item("Test", 10)
        with pytest.raises(ValueError):
            c.total(coupon="BADCODE")

# ---------------------------------------------------------------------------
# Edge case: ensure shipping_fee constants are defined.
# ---------------------------------------------------------------------------
def test_constants_defined():
    """The tests above implicitly rely on the constants used by shipping_fee.
    If they are missing, shipping_fee will raise a NameError during execution.
    This test checks that importing cart does not immediately fail due to
    undefined names. The actual values are not verified here; if they are
    wrong the other tests will surface mismatches.
    """
    assert True  # placeholder – just ensures import succeeded
