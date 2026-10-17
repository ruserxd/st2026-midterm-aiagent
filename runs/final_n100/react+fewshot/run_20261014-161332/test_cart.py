import pytest
import cart

# Helper: list of bulk discount percent expectations
bulk_cases = [
    (1, 0), (9, 0), (10, 5), (49, 5),
    (50, 10), (99, 10), (100, 15), (150, 15)
]

# -------------------- apply_discount --------------------
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (0.0,   0, 0.0),
    (100.0, 50, 50.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),          # negative price
    (100, -5),         # negative percent
    (100, 105),        # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# -------------------- bulk_discount_percent --------------------
@pytest.mark.parametrize("quantity,result", bulk_cases)
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# -------------------- parse_coupon --------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "",                # empty string
    "SAVE0",           # out of range 1-50
    "SAVE51",
    "DISCOUNT10",     # wrong prefix
    "SAVEXX",         # non‑numeric suffix
    "  SAVE -5  ",   # negative number
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# -------------------- shipping_fee --------------------
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------------------- Cart class --------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert list(self.cart.items()) == []

    def test_add_item_new(self):
        self.cart.add_item("Apple", 1.5, 2)
        items = dict(self.cart.items())
        assert items["Apple"] == (1.5, 2)

    def test_add_item_existing_same_price(self):
        self.cart.add_item("Banana", 0.75, 3)
        self.cart.add_item("Banana", 0.75, 2)
        assert dict(self.cart.items())["Banana"] == (0.75, 5)

    def test_add_item_existing_different_price_raises(self):
        self.cart.add_item("Orange", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", 1.2, 1)

    def test_remove_item_partial(self):
        self.cart.add_item("Grape", 2.0, 5)
        self.cart.remove_item("Grape", 3)
        assert dict(self.cart.items())["Grape"] == (2.0, 2)

    def test_remove_item_all_and_below(self):
        self.cart.add_item("Peach", 1.8, 4)
        self.cart.remove_item("Peach", 5)  # should remove item entirely
        assert "Peach" not in dict(self.cart.items())

    def test_remove_nonexistent_item_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Mango")

    def test_subtotal(self):
        self.cart.add_item("Bread", 2.5, 2)
        self.cart.add_item("Milk", 1.0, 3)
        assert self.cart.subtotal() == 2.5*2 + 1.0*3

    def test_total_no_discount(self):
        self.cart.add_item("Book", 12.0, 1)   # subtotal = 12.0
        # No coupon, member=False => shipping 60
        assert self.cart.total() == round(12.0 + 60, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("Notebook", 5.0, 10)   # subtotal = 50.0
        coupon_code = "SAVE10"
        # apply coupon: 10% off -> 45.0
        # shipping for member: half of 60 => 30
        expected_total = round(45.0 + 30, 2)
        assert self.cart.total(member=True, coupon=coupon_code) == expected_total

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_zero_cost(self):
        # Empty cart: subtotal 0, shipping waived
        assert self.cart.total() == 0.00
