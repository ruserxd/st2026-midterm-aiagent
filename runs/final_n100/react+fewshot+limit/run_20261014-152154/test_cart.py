import pytest
import cart

# ----- apply_discount -----

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary conditions and rounding
assert round(99 * 0.95, 2) == 94.05  # not needed as formula

@pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (50, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----
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

@pytest.mark.parametrize("quantity", [0, -5, 2.5, "10"])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SAVE30  ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV5",         # N < 1
    "SAVE51",       # N > 50
    "INVALID",      # wrong prefix
    "save-10",      # negative number
    "",             # empty
    "   ",         # only whitespace
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.5, 2)
        self.cart.add_item("banana", 0.5, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_mismatch_price(self):
        self.cart.add_item("pear", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 2.0, 1)

    def test_add_item_invalid_unit_or_qty(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, 2.5)

    def test_remove_item(self):
        self.cart.add_item("mango", 3.0, 4)
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {"mango": 2}
        # remove remaining to trigger deletion
        self.cart.remove_item("mango", 2)
        assert "mango" not in self.cart.items()

    def test_remove_item_negative_remaining(self):
        self.cart.add_item("grape", 0.8, 3)
        # removing more than present should delete item but no exception
        self.cart.remove_item("grape", 5)
        assert "grape" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_simple(self):
        # quantity <10 -> 0% discount
        self.cart.add_item("item1", 20.0, 5)
        assert self.cart.subtotal() == 100.0

    def test_subtotal_with_discounts(self):
        # item2: 12 units -> 5% discount on line total
        self.cart.add_item("item2", 10.0, 12)  # 120 * .95 = 114
        assert round(114, 2) == 114.0
        # subtotal should be sum of all lines: 100 + 114 = 214
        assert self.cart.subtotal() == 214.0

    def test_total_no_coupon_member(self):
        self.cart.add_item("item", 200.0, 1)
        # subtotal 200, no discount, shipping 60
        assert self.cart.total(member=False) == round(200 + 60, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("book", 120.0, 1)
        # subtotal 120, coupon SAVE10 -> 108
        # shipping for member: half of 60 = 30
        assert self.cart.total(member=True, coupon="SAVE10") == round(108 + 30, 2)

    def test_total_invalid_coupon(self):
        self.cart.add_item("pen", 5.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_items_immutable_copy(self):
        self.cart.add_item("item", 1.0, 2)
        items = self.cart.items()
        items["item"] = 10
        # internal should not change
        assert self.cart.items()["item"] == 2
