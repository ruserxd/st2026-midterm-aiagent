import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount --------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),
        (100.00, 0, 100.0),
        (50.5, 10, 45.45),  # 50.5*0.9 = 45.45
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 105],
)
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent -------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",
        "SAVE51",
        "SAVEXX",
        "",
        "  ",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (2000, True, 0),
        (999.99, False, 60),
        (999.99, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart -------------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initial_state(self):
        assert list(self.cart.items()) == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 60.0  # default subtotal 0, non‑member shipping 60

    def test_add_item_and_subtotal(self):
        self.cart.add_item("apple", 1.5, quantity=3)
        self.cart.add_item("banana", 2.0, quantity=2)
        assert set(name for name, _, _ in self.cart.items()) == {"apple", "banana"}
        expected_subtotal = 3 * 1.5 + 2 * 2.0
        assert self.cart.subtotal() == expected_subtotal

    def test_remove_item(self):
        self.cart.add_item("orange", 3.0, quantity=5)
        self.cart.remove_item("orange", quantity=2)
        # Remaining quantity should be 3
        assert next((q for n, _, q in self.cart.items() if n == "orange"), None) == 3
        self.cart.remove_item("orange", quantity=3)
        assert all(n != "orange" for n, _, _ in self.cart.items())

    def test_total_with_member_and_coupon(self):
        # Add items that trigger bulk discount on a single item type
        self.cart.add_item("widget", 10.0, quantity=120)  # bulk discount 15%
        subtotal = 120 * 10.0
        discounted_subtotal = apply_discount(subtotal, bulk_discount_percent(120))
        shipping = shipping_fee(discounted_subtotal, member=True)
        expected_total = discounted_subtotal + shipping
        assert self.cart.total(member=True) == pytest.approx(expected_total)

    def test_total_with_coupon(self):
        self.cart.add_item("thing", 50.0, quantity=2)
        subtotal = 100.0
        # coupon SAVE10 gives 10% discount
        expected_total = apply_discount(subtotal, parse_coupon("SAVE10")) + shipping_fee(100.0, member=False)
        assert self.cart.total(coupon="SAVE10") == pytest.approx(expected_total)

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("gadget", 200.0, quantity=1)
        subtotal = 200.0
        coupon_discount = parse_coupon("SAVE20")
        discounted_subtotal = apply_discount(subtotal, coupon_discount)
        shipping = shipping_fee(discounted_subtotal, member=True)
        expected_total = discounted_subtotal + shipping
        assert self.cart.total(member=True, coupon="SAVE20") == pytest.approx(expected_total)

    def test_add_and_remove_invalid_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("invalid", 5.0, quantity=0)
        with pytest.raises(ValueError):
            self.cart.remove_item("nonexistent", quantity=-1)
