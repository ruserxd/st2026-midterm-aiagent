import pytest
import cart

# ----------------------------
# Tests for standalone functions
# ----------------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ]
)
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [
        (-10, 20),                 # negative price
        (50, -5),                  # negative percent
        (30, 105),                 # percent >100
    ]
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),                    # less than 10
        (10, 5),                   # at threshold
        (49, 5),                   # just below 50
        (50, 10),                  # at threshold
        (99, 10),                  # just below 100
        (100, 15),                 # at threshold
    ]
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    "code,result",
    [
        ("SAVE10", 10),
        ("save20 ", 20),     # case-insensitive, trailing space
        ("  SaVe5", 5),      # leading/trailing spaces
    ]
)
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "",                # empty
    "INVALID",         # no SAVE prefix
    "SAVE0",           # below 1
    "SAVE51",          # above 50
    "save-5",          # negative
    "SAVExx",          # non-integer
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (500, False, 60),      # <1000, non-member
        (800, True, 30),       # <1000, member
        (1000, False, 0),      # exactly free threshold
        (1500, True, 0),       # >1000
    ]
)
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member=member) == result

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----------------------------
# Tests for Cart class behavior
# ----------------------------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty_cart(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_and_remove_items(self):
        # Add item A with price 20, qty 3 (no discount yet)
        self.cart.add_item("A", 20, quantity=3)
        assert self.cart.items() == {"A": 3}
        # Adding same item increases qty
        self.cart.add_item("A", 20, quantity=2)
        assert self.cart.items() == {"A": 5}
        # Add another item B
        self.cart.add_item("B", 10, quantity=1)
        assert set(self.cart.items().keys()) == {"A", "B"}
        # Remove some from A
        self.cart.remove_item("A", quantity=2)
        assert self.cart.items()["A"] == 3
        # Removing all of B removes it
        self.cart.remove_item("B")
        assert "B" not in self.cart.items()

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("C", -5, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("D", 10, quantity=0)
        # Adding same item with different price
        self.cart.add_item("E", 15, quantity=2)
        with pytest.raises(ValueError):
            self.cart.add_item("E", 20, quantity=1)

    def test_remove_invalid(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_bulk_discount(self):
        # 12 units of X at $5 each: bulk discount 5%
        self.cart.add_item("X", 5, quantity=12)
        expected = round(5 * 12 * (1 - 0.05), 2)  # 12*5=60, minus 3
        assert self.cart.subtotal() == expected
        # No bulk discount for less than 10
        self.cart.add_item("Y", 10, quantity=9)
        total_no_disc = round(10 * 9, 2)  # 90
        # subtotal is sum of both items
        assert self.cart.subtotal() == expected + total_no_disc

    def test_total_with_coupon_and_shipping(self):
        # Add items totaling $200 with no bulk discount
        self.cart.add_item("Item1", 50, quantity=4)  # 200
        # Apply coupon SAVE10 -> 10% off: $180
        total = self.cart.total(coupon="SAVE10")
        assert total == round(180 + cart.shipping_fee(180), 2)
        # Member should pay half shipping on same amount
        member_total = self.cart.total(member=True, coupon="SAVE10")
        assert member_total == round(180 + cart.shipping_fee(180, member=True), 2)

    def test_total_with_large_subtotal_free_shipping(self):
        # Add items totaling $1200 >1000, free shipping
        self.cart.add_item("Expensive", 300, quantity=4)  # 1200
        total = self.cart.total()
        assert total == round(1200 + 0, 2)

    def test_total_invalid_coupon(self):
        self.cart.add_item("Cheap", 10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
