import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
    (123.456, 10, 111.11),     # rounding to 2 decimals
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -5, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (0, 0),      # should raise ValueError because quantity must be positive integer
    (1, 0),      # below threshold
    (10, 5),     # exact threshold
    (49, 5),     # just below 50
    (50, 10),    # exact threshold
    (99, 10),    # just below 100
    (100, 15),   # exact threshold
    (150, 15),   # above
])
def test_bulk_discount_percent(quantity, expected):
    if quantity <= 0:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(quantity)
    else:
        assert cart.bulk_discount_percent(quantity) == expected

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE25 ", 25),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# error cases for parse_coupon
@pytest.mark.parametrize("code", [
    "SAVEXX",          # invalid prefix
    "SAVE0",           # N out of range (1-50)
    "SAVE51",          # N too high
    "NOTACODE",
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
    (800, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# error cases for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty_cart(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # add_item tests
    @pytest.mark.parametrize("name,unit_price,quantity", [
        ("apple", 2.0, 1),
        ("banana", 1.5, 3),
    ])
    def test_add_single_item(self, name, unit_price, quantity):
        self.cart.add_item(name, unit_price, quantity)
        assert self.cart.items() == {name: quantity}

    def test_add_existing_item_same_price_increases_quantity(self):
        self.cart.add_item("orange", 3.0, 2)
        self.cart.add_item("orange", 3.0, 4)
        assert self.cart.items() == {"orange": 6}

    def test_add_existing_item_different_price_raises(self):
        self.cart.add_item("kiwi", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("kiwi", 2.0, 1)

    # error cases for add_item
    @pytest.mark.parametrize("unit_price,quantity", [(-1, 1), (5, -3)])
    def test_add_item_invalid_params(self, unit_price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("mango", unit_price, quantity)

    # remove_item tests
    def test_remove_item_decreases_quantity_and_removes_if_zero(self):
        self.cart.add_item("pear", 2.5, 3)
        self.cart.remove_item("pear", 1)
        assert self.cart.items() == {"pear": 2}
        self.cart.remove_item("pear", 2)  # should remove completely
        assert self.cart.items() == {}

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    # subtotal calculation including bulk discounts and rounding
    def test_subtotal_with_bulk_discounts_and_rounding(self):
        # quantity 12 -> 5% discount, 7 -> no discount
        self.cart.add_item("itemA", 10.0, 12)  # discounted unit price = 9.5
        self.cart.add_item("itemB", 3.333, 7)   # no discount, price stays
        expected = round(12 * 9.5 + 7 * 3.333, 2)
        assert self.cart.subtotal() == expected

    # total calculation with coupon and shipping
    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("gift", 500.0, 1)   # subtotal 500
        # apply coupon SAVE20 -> 20% off => 400
        total = self.cart.total(member=False, coupon="SAVE20")
        # shipping fee on 400 -> 60 (not member)
        expected_total = round(400 + 60, 2)
        assert total == expected_total

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("book", 30.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
