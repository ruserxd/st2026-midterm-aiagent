import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price
@pytest.mark.parametrize("price,percent", [(-1, 10), (5, -1), (5, 101)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),     # below 10
    (10, 5),    # threshold 10
    (49, 5),    # just under 50
    (50, 10),   # threshold 50
    (99, 10),   # just under 100
    (100, 15),  # threshold 100
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "INVALID",
    "SAVE0",
    "SAVE51",
    "save-5",
    "SAVExx",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),          # free for >=1000
    (1500, True, 0),           # also free
    (999.99, False, 60),       # under threshold
    (200, True, 30),           # member half
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        # add new item
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}
        # add more of same name with same price
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1.0, 1)   # negative price
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)    # non‑positive quantity

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 2.5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 3.0, 1)   # price differs

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("pear", 4.0, 5)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 3}
        # remove remaining quantity to delete item
        self.cart.remove_item("pear", 3)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_subtotal_with_bulk_discount(self):
        # 12 apples, price 1 each -> bulk discount 5%
        self.cart.add_item("apple", 1.0, 12)
        expected = round(1.0 * 12 * (1 - 0.05), 2)  # 11.4
        assert self.cart.subtotal() == expected

    def test_subtotal_empty(self):
        assert self.cart.subtotal() == 0

    def test_total_no_coupon_or_member(self):
        # 10 bananas, price 2 each -> no bulk discount
        self.cart.add_item("banana", 2.0, 10)
        subtotal = 20.0
        shipping = cart.shipping_fee(subtotal)  # 60 (subtotal <1000)
        total_expected = round(subtotal + shipping, 2)
        assert self.cart.total() == total_expected

    def test_total_with_coupon_and_member(self):
        # 5 cherries, price 3 each -> no bulk discount
        self.cart.add_item("cherry", 3.0, 5)
        subtotal = 15.0
        # apply coupon SAVE10 => 10% off subtotal
        after_coupon = cart.apply_discount(subtotal, 10)  # 13.5
        shipping = cart.shipping_fee(after_coupon, member=True)  # 30 half
        total_expected = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == total_expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("kiwi", 5.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
