import pytest
import cart

# ---------------------------
# Helper functions for expected values
# ---------------------------

def discounted_price(unit_price, percent):
    return round(unit_price * (1 - percent / 100), 2)

# --------------- apply_discount tests -------------------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),  # simple case
        (50.0, 0, 50.0),     # no discount
        (100.0, 100, 0.0),   # full discount
        (123.45, 12.5, round(123.45 * 0.875, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -10.5])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-1, 101, 150],
) 
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100.0, percent)

# --------------- bulk_discount_percent tests -------------------

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0), (9, 0),      # below threshold
        (10, 5), (19, 5),
        (50, 10), (99, 10),
        (100, 15), (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5, "10"])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------------- parse_coupon tests -------------------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE50 ", 50),
        ("sAvE1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",      # missing 'E'
    "SAVE0",      # below min value
    "SAVE51",     # above max value
    "SAVEabc",    # non-numeric N
    "save -5",   # negative number with space
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------------- shipping_fee tests -------------------

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000.0, False, 0),   # free
        (1500.0, True, 0),    # free even if member
        (999.99, False, 60),  # not free, non-member
        (200.0, True, 30),    # half fee for member
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------------- Cart tests -------------------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # Add item tests
    def test_add_item_new(self):
        self.cart.add_item("Apple", 2.5, quantity=3)
        assert self.cart.items() == {"Apple": 3}
        # unit price stored implicitly; subtotal uses it
        expected = discounted_price(2.5, cart.bulk_discount_percent(3)) * 3
        assert self.cart.subtotal() == round(expected, 2)

    def test_add_item_existing_same_price(self):
        self.cart.add_item("Banana", 1.0, quantity=2)
        self.cart.add_item("Banana", 1.0, quantity=4)
        assert self.cart.items() == {"Banana": 6}

    def test_add_item_mismatched_price_raises(self):
        self.cart.add_item("Orange", 3.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", 2.5, quantity=2)

    @pytest.mark.parametrize("unit_price, qty", [(-5.0, 1), (1.0, 0), (2.0, -3)])
    def test_add_item_invalid_inputs_raises(self, unit_price, qty):
        with pytest.raises(ValueError):
            self.cart.add_item("Grape", unit_price, quantity=qty)

    # Remove item tests
    def test_remove_item_partial_and_zero(self):
        self.cart.add_item("Peach", 4.0, quantity=5)
        self.cart.remove_item("Peach", quantity=2)
        assert self.cart.items() == {"Peach": 3}
        # remove the rest
        self.cart.remove_item("Peach", quantity=3)
        assert "Peach" not in self.cart.items()

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Mango", quantity=1)

    # items returns copy
    def test_items_returns_copy(self):
        self.cart.add_item("Kiwi", 2.0, quantity=3)
        it = self.cart.items()
        it["Kiwi"] = 10
        assert self.cart.items()["Kiwi"] == 3

    # subtotal discount calculations
    def test_subtotal_with_bulk_discounts(self):
        # Item A: qty 5 -> no discount, price 10
        self.cart.add_item("A", 10.0, quantity=5)
        # Item B: qty 12 -> 5% discount, price 20
        self.cart.add_item("B", 20.0, quantity=12)
        # Item C: qty 55 -> 10% discount, price 5
        self.cart.add_item("C", 5.0, quantity=55)
        # Calculate expected subtotal manually
        expected_a = 10.0 * 5  # no discount
        expected_b = discounted_price(20.0, 5) * 12
        expected_c = discounted_price(5.0, 10) * 55
        expected_subtotal = round(expected_a + expected_b + expected_c, 2)
        assert self.cart.subtotal() == expected_subtotal

    # total with coupon and shipping
    def test_total_with_coupon_and_shipping_member(self):
        # Build cart: subtotal after discount but before coupon < 1000 to trigger shipping
        self.cart.add_item("Large", 300.0, quantity=3)  # qty 3 -> no bulk discount
        # Subtotal = 900.0
        # Apply coupon SAVE10 => reduce by 10% => 810.0
        total_after_coupon = cart.apply_discount(900.0, 10)
        # Shipping fee for non-member would be 60; member gets half -> 30
        expected_total = round(total_after_coupon + 30, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == pytest.approx(expected_total, rel=1e-9)

    def test_total_with_free_shipping(self):
        # Cart subtotal after discount >=1000 to get free shipping
        self.cart.add_item("Expensive", 500.0, quantity=3)  # qty 3 -> no bulk
        # Subtotal = 1500
        # Apply coupon SAVE20 => reduce by 20% => 1200
        total_after_coupon = cart.apply_discount(1500.0, 20)
        # Shipping free regardless of member status
        expected_total = round(total_after_coupon + 0, 2)
        assert self.cart.total(member=False, coupon="SAVE20") == pytest.approx(expected_total, rel=1e-9)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("Item", 50.0, quantity=2)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_empty_cart_no_shipping_and_zero_cost(self):
        assert self.cart.total() == 0.0

# Run the tests if this file is executed directly (optional)
if __name__ == "__main__":
    pytest.main([__file__])
