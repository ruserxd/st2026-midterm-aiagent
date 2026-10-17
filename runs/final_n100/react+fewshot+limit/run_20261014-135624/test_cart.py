import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.00),   # example from spec
        (100, 0, 100.00),    # no discount
        (50, 100, 0.00),     # full discount
        (99.999, 10, round(99.999*0.9,2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Edge: invalid price or percent
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (50, 120)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0), (9, 0),  # below thresholds
        (10, 5), (49, 5),
        (50, 10), (99, 10),
        (100, 15), (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Edge: invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("sAvE05", 5),  # lower bound
        ("SAVE50", 50),   # upper bound
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEBAD", "NOPE", "save-5", "SAVE51", "SA VE10", " "])  # invalid formats
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (500, False, 60),   # non-member under threshold
        (800, True, 30),    # member under threshold
        (1000, False, 0),   # free for any
        (1200, True, 0),    # free for members
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Edge: negative subtotal
@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_and_items(self):
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple": 2}

    def test_add_existing_item_increases_quantity(self):
        self.cart.add_item("banana", 0.50, 3)
        self.cart.add_item("banana", 0.50, 2)
        assert self.cart.items() == {"banana": 5}

    def test_add_item_same_name_different_price_raises(self):
        self.cart.add_item("cherry", 0.30, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("cherry", 0.35, 1)

    def test_remove_item_decreases_quantity_and_removes_when_zero(self):
        self.cart.add_item("date", 2.00, 4)
        self.cart.remove_item("date", 3)
        assert self.cart.items() == {"date": 1}
        self.cart.remove_item("date", 1)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("fig", 1)

    def test_subtotal_calculation_with_bulk_discount(self):
        # 5 apples at $10 each -> no bulk discount
        self.cart.add_item("apple", 10.00, 5)
        # 12 oranges at $5 each -> bulk discount 5%
        self.cart.add_item("orange", 5.00, 12)
        # Expected: apple subtotal = 50.00
        # orange subtotal before discount = 60.00; after 5% -> 57.00
        expected_subtotal = round(50.00 + 57.00, 2)
        assert self.cart.subtotal() == expected_subtotal

    def test_total_with_coupon_and_shipping(self):
        # Add items to produce subtotal $1200 (free shipping), apply coupon
        self.cart.add_item("item", 200.00, 6)   # no bulk discount, subtotal = 1200
        subtotal = self.cart.subtotal()
        assert subtotal == 1200.00
        # Apply a valid coupon of 10%
        total_with_coupon = cart.apply_discount(subtotal, 10)
        # shipping on discounted amount: subtotal_after_coupon >=1000 -> free
        expected_total = round(total_with_coupon + 0, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 1.00, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_zero_and_no_shipping(self):
        assert self.cart.total() == 0.00
