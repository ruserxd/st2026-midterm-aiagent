import pytest
import cart

# ---- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary checks for validation
@pytest.mark.parametrize(
    "price, percent",
    [
        (-1, 10),                 # negative price
        (100, -5),                # negative percent
        (100, 105),               # percent > 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent ----------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),     # below 10
        (10, 5),    # exactly 10
        (49, 5),    # just below 50
        (50, 10),   # exactly 50
        (99, 10),   # just below 100
        (100, 15),  # exactly 100
        (150, 15),  # above 100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),            # case‑insensitive
        (" SAVE30 ", 30),          # whitespace ignored
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",       # missing SAVE prefix
    "SAVE0",      # N < 1
    "SAVE51",     # N > 50
    "ABC123",     # unrelated code
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (999.99, False, 60),   # below free threshold
        (1000, False, 0),      # exactly at threshold
        (1500, True, 30),      # member gets half
        (2000, True, 0),       # member with free shipping
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class --------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert list(self.cart.items().keys()) == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.00, 5)
        assert self.cart.items()["apple"] == 5
        # adding same item increases quantity; price must match
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items()["apple"] == 8
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 2.00, 1)  # price mismatch

    def test_add_item_validation(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 1.5)

    def test_remove_item(self):
        self.cart.add_item("orange", 2.0, 4)
        # remove fewer than quantity
        self.cart.remove_item("orange", 2)
        assert self.cart.items()["orange"] == 2
        # removing the rest removes the item completely
        self.cart.remove_item("orange", 2)
        assert "orange" not in self.cart.items()
        # removing non‑existent key raises KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_bulk_discount(self):
        # 10 items, unit price 5 -> bulk discount 5% on each
        self.cart.add_item("widget", 5.0, 10)
        expected = round(5.0 * 10 * (1 - 0.05), 2)  # 47.5
        assert self.cart.subtotal() == expected

    def test_total_no_coupon(self):
        self.cart.add_item("gadget", 200, 6)   # 6 items, no bulk discount
        # subtotal = 1200, shipping free, total = 1200
        assert self.cart.total(member=True) == 1200.00

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("toy", 100, 5)   # 5 items -> bulk discount 5%
        subtotal = round(100 * 5 * (1 - 0.05), 2)   # 475.00
        # apply coupon SAVE10 => 10% off
        after_coupon = round(subtotal * (1 - 0.10), 2)  # 427.50
        # shipping fee for non‑member on amount <1000 -> 60
        total_expected = round(after_coupon + 60, 2)    # 487.50
        assert self.cart.total(member=False, coupon="SAVE10") == total_expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("book", 20, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_empty_cart_no_shipping(self):
        # empty cart should not charge shipping
        assert self.cart.total() == 0.0
        assert self.cart.total(member=True) == 0.0
