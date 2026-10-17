import pytest
import cart

# ---------- Helper constants for expected values ----------
BASE_CURRENCY = "USD"

# ---------- Tests for utility functions ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (50.0, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Boundary and error tests for apply_discount
@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (30, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Bulk discount percent tests
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
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

# Errors for negative or non‑int quantity
@pytest.mark.parametrize(
    "quantity",
    [0, -3, 4.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Coupon parsing tests – case and whitespace tolerant
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30  ", 30),
        ("saVE1", 1),
        ("SAVE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupon formats
@pytest.mark.parametrize(
    "code",
    ["SAV10", "SAVE0", "SAVE51", "SAVExx", "", "  "] ,
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee logic
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
    assert cart.shipping_fee(subtotal, member) == expected

# Errors for negative subtotal
with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- Tests for the Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # Adding items – basic and bulk discounts
    def test_add_item_basic_and_bulk(self):
        # Add a single unit, no bulk discount
        self.cart.add_item("Widget", 20.0)
        assert self.cart.items() == {"Widget": 1}
        assert self.cart.subtotal() == 20.0
        # Add more units to trigger a bulk discount (10 items → 5%)
        for _ in range(9):
            self.cart.add_item("Widget", 20.0)
        assert self.cart.items()["Widget"] == 10
        expected = 20.0 * 10 * cart.apply_discount(1, 5)  # 5% off each unit
        assert self.cart.subtotal() == round(expected, 2)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("Gadget", 15.0)
        with pytest.raises(ValueError):
            self.cart.add_item("Gadget", 12.5)  # price must match existing

    # Removing items – partial and complete removal
    def test_remove_partial_and_complete(self):
        self.cart.add_item("Thingamajig", 10.0, quantity=3)
        self.cart.remove_item("Thingamajig")
        assert self.cart.items()["Thingamajig"] == 2
        self.cart.remove_item("Thingamajig", quantity=2)
        assert "Thingamajig" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("NonExistent")

    # Total calculation – coupons, shipping, member discounts
    def test_total_with_coupon_and_shipping(self):
        # 3 items at $100 each: subtotal = 300.00
        self.cart.add_item("Premium", 100.0, quantity=3)
        # Apply a valid coupon of 10%
        total_before_shipping = cart.apply_discount(300.0, 10)  # 270.0
        # Non‑member shipping fee on 270 is 60
        expected_total = round(total_before_shipping + 60, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_with_member_and_bulk(self):
        # 120 units of an item priced $5 -> bulk discount 15%
        for _ in range(120):
            self.cart.add_item("BulkItem", 5.0)
        subtotal = cart.apply_discount(5.0 * 120, 15)  # 60%? actually 15%
        subtotal = round(subtotal, 2)
        # Shipping should be free (subtotal > 1000)
        assert self.cart.total(member=True) == round(subtotal + 0, 2)

    def test_total_invalid_coupon(self):
        self.cart.add_item("Item", 50.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
