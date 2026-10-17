import pytest
import cart

# --------------------
# Helper constants
MAX_DISCOUNT = 100

# ---------- apply_discount ---------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),      # example from spec
    (100, 0, 100.0),       # no discount
    (50, 100, 0.0),        # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary conditions for price and percent
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -1])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ---------
@pytest.mark.parametrize("qty, expected", [
    (5, 0),   # less than 10
    (10, 5),  # exactly 10
    (49, 5),  # just below 50
    (50, 10), # exactly 50
    (99, 10), # just below 100
    (100, 15),# exactly 100
    (150, 15) # above 100
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 1.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# ---------- parse_coupon ---------
valid_coupons = {
    "SAVE10": 10,
    "save25": 25,
    " SAVE50 ": 50,
    "SaVe1": 1
}

@pytest.mark.parametrize("code, expected", valid_coupons.items())
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["INVALID", "SAVE0", "SAVE51", "SAVEXY", "save-10", "  "]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initially(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    # add_item tests
    @pytest.mark.parametrize("name, unit_price, qty", [
        ("apple", 1.00, 3),
        ("banana", 2.50, 10)
    ])
    def test_add_new_items(self, name, unit_price, qty):
        self.cart.add_item(name, unit_price, qty)
        assert self.cart.items()[name] == qty

    def test_add_existing_item_increments_quantity(self):
        self.cart.add_item("orange", 0.80, 2)
        self.cart.add_item("orange", 0.80, 3)
        assert self.cart.items()["orange"] == 5

    def test_add_item_with_different_price_raises(self):
        self.cart.add_item("pear", 1.20, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.30, 2)

    @pytest.mark.parametrize("unit_price", [-0.01, -5])
    def test_add_item_negative_price_raises(self, unit_price):
        with pytest.raises(ValueError):
            self.cart.add_item("fig", unit_price, 1)

    @pytest.mark.parametrize("qty", [0, -3, 2.5])
    def test_add_item_invalid_qty_raises(self, qty):
        with pytest.raises(ValueError):
            self.cart.add_item("grape", 1.00, int(qty))

    # remove_item tests
    def test_remove_partial_quantity(self):
        self.cart.add_item("mango", 2.00, 5)
        self.cart.remove_item("mango", 2)
        assert self.cart.items()["mango"] == 3

    def test_remove_entire_quantity_removes_item(self):
        self.cart.add_item("peach", 1.50, 4)
        self.cart.remove_item("peach", 4)
        assert "peach" not in self.cart.items()

    def test_remove_more_than_exists_does_not_raise_but_removes(self):
        self.cart.add_item("plum", 0.90, 2)
        self.cart.remove_item("plum", 5)
        assert "plum" not in self.cart.items()

    def test_remove_nonexistent_item_raises_keyerror(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    # subtotal calculations with bulk discounts
    def test_subtotal_with_bulk_discount(self):
        # 10 apples => 5% discount on each apple
        self.cart.add_item("apple", 2.00, 10)
        # expected per-apple price after discount: 1.90
        expected = 2.00 * 10 * (1 - 0.05)
        assert round(self.cart.subtotal(), 2) == round(expected, 2)

    def test_subtotal_multiple_items(self):
        self.cart.add_item("apple", 3.00, 5)   # no discount
        self.cart.add_item("banana", 1.00, 50)  # 10% discount on banana
        subtotal_apple = 3.00 * 5
        subtotal_banana = 1.00 * 50 * (1 - 0.10)
        expected = round(subtotal_apple + subtotal_banana, 2)
        assert self.cart.subtotal() == expected

    # total with member flag and coupon
    def test_total_no_member_no_coupon(self):
        self.cart.add_item("item", 100.0, 1)
        expected = 100.0 + cart.shipping_fee(100.0, False)
        assert self.cart.total() == round(expected, 2)

    def test_total_with_member_ships_half(self):
        self.cart.add_item("item", 200.0, 1)
        subtotal = 200.0
        shipping = cart.shipping_fee(subtotal, True)  # should be 30
        expected = round(subtotal + shipping, 2)
        assert self.cart.total(member=True) == expected

    def test_total_with_coupon_discount(self):
        self.cart.add_item("item", 200.0, 1)
        subtotal = 200.0
        # coupon 'SAVE10' gives 10% off on items before shipping
        discount = cart.apply_discount(subtotal, 10)  # 180
        shipping = cart.shipping_fee(discount, False)
        expected = round(discount + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("item", 1200.0, 1)
        subtotal = 1200.0
        discount = cart.apply_discount(subtotal, 15)  # 1020
        shipping = cart.shipping_fee(discount, True)  # free because >=1000 after discount
        expected = round(discount + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE15") == expected
