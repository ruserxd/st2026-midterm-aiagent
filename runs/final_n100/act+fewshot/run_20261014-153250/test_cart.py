import pytest
import cart

# ---------- basic helper assertions for rounding

def assert_close(a, b, tol=1e-9):
    assert abs(a - b) < tol, f"{a} not close to {b}"

# ---- tests for apply_discount -------------------------------------------------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),   # example
        (100, 0, 100.0),     # no discount
        (50, 100, 0.0),      # full discount
        (123.456, 33, round(123.456 * 0.67, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid inputs ---------------------------------------------------------------
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 150, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent -----------------------------------------------------

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (250, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon --------------------------------------------------------------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid codes: wrong prefix, non-integer, out of bounds, extra chars
@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "SAVE-5", "ABCD", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -------------------------------------------------------------

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart tests ---------------------------------------------------------------

class TestCartBasic:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_subtotal_and_total(self):
        assert self.cart.subtotal() == 0
        # total with no coupon and non-member: shipping should not be applied
        assert self.cart.total(member=False) == 0
        # even with member or coupon, empty cart stays zero
        assert self.cart.total(member=True, coupon="SAVE10") == 0

    def test_add_and_items(self):
        self.cart.add_item("apple", 2.5)
        self.cart.add_item("banana", 1.2, quantity=3)
        # adding same item increases qty if price matches
        self.cart.add_item("apple", 2.5, quantity=2)
        assert self.cart.items() == {"apple": 3, "banana": 3}

    def test_add_same_name_different_price_raises(self):
        self.cart.add_item("widget", 10.0)
        with pytest.raises(ValueError):
            self.cart.add_item("widget", 12.0)

    def test_remove_item_decreases_quantity_and_removes_when_zero(self):
        self.cart.add_item("toy", 5.0, quantity=5)
        self.cart.remove_item("toy", quantity=3)
        assert self.cart.items() == {"toy": 2}
        # removing remaining items removes key
        self.cart.remove_item("toy", quantity=2)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_with_bulk_discount(self):
        # 10 apples, bulk discount 5%
        self.cart.add_item("apple", 1.0, quantity=10)
        expected = round(1.0 * 10 * (1 - 0.05), 2)  # 9.5
        assert self.cart.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        # Add items to exceed shipping threshold after coupon
        self.cart.add_item("item", 200, quantity=3)  # 600 subtotal
        # Apply a 10% coupon -> 540
        total = self.cart.total(member=False, coupon="SAVE10")
        # Shipping: 60 because 540 < 1000 and non-member
        expected_total = round(540 + 60, 2)
        assert total == expected_total

    def test_member_shipping_free_on_threshold(self):
        self.cart.add_item("expensive", 400, quantity=3)  # 1200 subtotal
        # No coupon
        total = self.cart.total(member=True)
        # Shipping should be free (subtotal >=1000 after no coupon)
        assert total == round(1200 + 0, 2)

    def test_coupon_invalid_raises(self):
        self.cart.add_item("stuff", 10)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
