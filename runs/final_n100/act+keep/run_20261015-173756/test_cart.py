import math
import pytest
import cart

# Helper to compare floating numbers with rounding
round2 = lambda x: round(float(x), 2)

# ---------- apply_discount --------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 20, round2(98.76)),  # 123.45*0.8
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert round2(cart.apply_discount(price, percent)) == round2(result)

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105), (0.1, 101)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVExx",
        "save0",
        "SAVE51",
        "",  # empty string
        "  ",
        "DISCOUNT10",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (500, True, 30),
        (1000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1.5],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state_empty(self):
        assert self.cart.items() == {}
        assert round2(self.cart.subtotal()) == 0.0
        assert round2(self.cart.total()) == 0.0

    def test_add_and_remove_item(self):
        self.cart.add_item("apple", 100, quantity=3)
        self.cart.add_item("banana", 50, quantity=2)
        assert self.cart.items() == {"apple": 3, "banana": 2}

        # subtotal with bulk discount: apple 3*100 =300 no disc; banana 2*50=100 no disc
        assert round2(self.cart.subtotal()) == 400.0

        # remove one banana
        self.cart.remove_item("banana", quantity=1)
        assert self.cart.items() == {"apple": 3, "banana": 1}
        assert round2(self.cart.subtotal()) == 350.0

    def test_bulk_discount_in_subtotal(self):
        # 10 apples => bulk discount 5%
        self.cart.add_item("apple", 20, quantity=10)
        expected = round2(20 * 10 * (1 - 0.05))
        assert round2(self.cart.subtotal()) == expected

    def test_total_with_coupon_and_shipping(self):
        # 20 bananas at $30 each -> subtotal 600; bulk discount 5% => 570
        self.cart.add_item("banana", 30, quantity=20)
        # coupon SAVE10 reduces 10%
        total_before_shipping = round2(570 * 0.9)
        shipping = cart.shipping_fee(total_before_shipping)
        expected_total = round2(total_before_shipping + shipping)
        assert round2(self.cart.total(coupon="SAVE10")) == expected_total

    def test_total_member_free_shipping_over_1000(self):
        # add items totalling 1100 before discount
        self.cart.add_item("widget", 1100, quantity=1)
        # no coupon; subtotal 1100 -> shipping free
        assert cart.shipping_fee(1100) == 0
        assert round2(self.cart.total(member=True)) == 1100.0

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0

    def test_invalid_coupon_raises(self):
        self.cart.add_item("item", 10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_remove_more_than_exists_does_not_error(self):
        self.cart.add_item("pen", 5, quantity=2)
        # Removing more than present should set to zero or keep positive
        self.cart.remove_item("pen", quantity=5)
        assert self.cart.items().get("pen", 0) == 0

    def test_add_negative_quantity_raises(self):
        with pytest.raises(ValueError):
            self.cart.add_item("paper", 2, quantity=-3)

    def test_remove_nonexistent_item_ignores(self):
        # Removing an item not in cart should leave items unchanged
        self.cart.remove_item("nonexist")
        assert self.cart.items() == {}
