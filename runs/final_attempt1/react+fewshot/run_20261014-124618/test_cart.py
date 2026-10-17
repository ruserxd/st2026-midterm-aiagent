import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),        # example
    (100, 0, 100.0),         # no discount
    (50, 100, 0.0),          # full discount
    (123.456, 10, 111.11),   # rounding to two decimals
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid cases
@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity, expected", [
    (1, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.14])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10), ("save20", 20), (" SAVE5 ", 5), ("SaVe50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEBAR", "10SAVE", "", "save-5", " saVe10 "])  # last includes space and wrong format
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60), (999.99, False, 60), (1000, False, 0), (1200, True, 0), (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple": 3}
        # adding existing with same unit_price increases qty
        self.cart.add_item("apple", 1.0, quantity=2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.5, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.5, quantity=-3)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 1.2, quantity=2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.5, quantity=1)

    def test_remove_item(self):
        self.cart.add_item("pear", 0.8, quantity=4)
        self.cart.remove_item("pear", quantity=2)
        assert self.cart.items() == {"pear": 2}
        # remove more than remaining -> should delete
        self.cart.remove_item("pear", quantity=5)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_no_discount(self):
        # 3 apples at $1 each, no discount
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.subtotal() == 3.0

    def test_subtotal_bulk_discount(self):
        # 10 oranges at $2 each => bulk discount 5%
        self.cart.add_item("orange", 2.0, quantity=10)
        line_total = 20.0
        discounted = cart.apply_discount(line_total, 5)  # 19.0
        assert self.cart.subtotal() == round(discounted, 2)

    def test_total_no_coupon_member(self):
        self.cart.add_item("item", 10.0, quantity=1)
        # subtotal 10, shipping 60 (non-member) => total 70
        assert self.cart.total(member=False) == 70.0

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 200.0, quantity=1)
        # subtotal 200, coupon SAVE10 -> 180, shipping 30 (member) => 210
        assert self.cart.total(member=True, coupon="SAVE10") == 210.0

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", 50.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
