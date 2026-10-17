import pytest
import cart

# --- apply_discount tests ---------------------------------------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (123.45, 25, round(123.45 * 0.75, 2)),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (100, -5), (100, 105)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests -------------------------------------------

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),     # below all thresholds
        (10, 5),    # threshold for 5%
        (49, 5),
        (50, 10),   # threshold for 10%
        (99, 10),
        (100, 15),  # threshold for 15%
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests -----------------------------------------------------

@pytest.mark.parametrize(
    "code,result",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("   SaVe5   ", 5),
    ],
)
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE51", "12345", " save10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests -----------------------------------------------------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),     # threshold
        (1200.50, True, 0),   # over threshold
        (999.99, False, 60),
        (500, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ------------------------------------------------------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert list(self.cart.items().keys()) == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # add_item
    def test_add_new_item(self):
        self.cart.add_item("Apple", 1.50, 3)
        assert self.cart.items() == {"Apple": 3}

    def test_add_existing_item_increases_qty_and_price_check(self):
        self.cart.add_item("Banana", 0.5, 2)
        with pytest.raises(ValueError):
            # price mismatch should raise
            self.cart.add_item("Banana", 0.6, 1)
        self.cart.remove_item("Banana", 1)  # remove one to test removal
        assert "Banana" not in self.cart.items()

    @pytest.mark.parametrize(
        "price,quantity",
        [(-5, 1), (10, -2), (0, 0)],
    )
    def test_add_item_invalid_args(self, price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", price, quantity)

    # remove_item
    def test_remove_partial_and_full_quantity(self):
        self.cart.add_item("Grapes", 2.0, 5)
        self.cart.remove_item("Grapes", 3)
        assert self.cart.items() == {"Grapes": 2}
        self.cart.remove_item("Grapes", 2)  # should remove item
        assert "Grapes" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("NonExistent", 1)

    # subtotal calculation with bulk discount
    def test_subtotal_with_bulk_discount(self):
        # Apple: qty 5 - no discount, price 10 = 50
        self.cart.add_item("Apple", 10.0, 5)
        # Banana: qty 15 - 5% discount, price 20 = 300*0.95=285
        self.cart.add_item("Banana", 20.0, 15)
        assert round(self.cart.subtotal(), 2) == round(50 + 285, 2)

    def test_total_with_coupon_and_shipping(self):
        # Add items totaling 1200 subtotal (no discount). Coupon reduces to 1000 = free shipping
        self.cart.add_item("Expensive", 400.0, 3)  # 1200
        total = self.cart.total(coupon="SAVE25")  # 25% off = 900, no shipping
        expected = round(1200 * 0.75, 2)
        assert total == expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("Item", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_member_shipping_half_fee(self):
        # subtotal 800 - shipping fee 60 unless member
        self.cart.add_item("MidCost", 200.0, 4)  # 800
        assert cart.shipping_fee(800, member=True) == 30
        total = self.cart.total(member=True)
        expected = round(800 + 30, 2)
        assert total == expected

    def test_total_no_items(self):
        assert self.cart.total() == 0.0
