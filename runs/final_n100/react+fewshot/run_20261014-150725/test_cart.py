import pytest
import cart

# helper for rounding checks
def round_two(x):
    return round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == round_two(result)

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (50, -5),
    (50, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2, "a"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25 ", 25),
    ("   SaVe5", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",          # missing S in SAVE
    "SAVE0",          # N out of range
    "SAVE51",         # N out of range
    "SAVE-5",         # negative number
    "save",           # no number
    "  ",            # only whitespace
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}
        assert round_two(self.cart.subtotal()) == 0.00
        assert round_two(self.cart.total()) == 0.00

    # adding items
    def test_add_item_new(self):
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple": 2}
        # unit price must match if added again
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 5}
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 99, 1)  # different price

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -10, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 10, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 10, "a")

    # removing items
    def test_remove_item(self):
        self.cart.add_item("pear", 200, 3)
        self.cart.remove_item("pear", 1)
        assert self.cart.items() == {"pear": 2}
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("orange", 1)

    # subtotal calculation
    def test_subtotal_no_discount(self):
        self.cart.add_item("tshirt", 1000, 1)  # <10 qty => no bulk discount
        assert round_two(self.cart.subtotal()) == 1000.00

    def test_subtotal_with_bulk(self):
        self.cart.add_item("mug", 200, 15)   # qty=15 -> 5% discount on this item
        expected = 200 * 15 * (1 - 0.05)
        assert round_two(self.cart.subtotal()) == round_two(expected)

    def test_subtotal_multiple_items(self):
        self.cart.add_item("itemA", 100, 10)   # 5% off on itemA
        self.cart.add_item("itemB", 50, 60)    # 10% off on itemB
        total = 100 * 10 * (1 - 0.05) + 50 * 60 * (1 - 0.10)
        assert round_two(self.cart.subtotal()) == round_two(total)

    # total calculation
    def test_total_no_coupon_member(self):
        self.cart.add_item("book", 800, 2)  # subtotal = 1600, shipping free
        assert round_two(self.cart.total(member=True)) == 1600.00

    def test_total_with_coupon_and_nonmember(self):
        """
        Subtotal: 200*3 = 600, coupon 20% -> 480, shipping 60 -> 540
        """
        self.cart.add_item("pen", 200, 3)
        assert round_two(self.cart.total(member=False, coupon="SAVE10")) == 540.00

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
