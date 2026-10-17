import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (123.456, 10, 111.11),  # rounding check
    (100, 0, 100.0),        # no discount
    (100, 100, 0.0)         # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (100, -5),
    (100, 105)
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (99, 0),   # just below 100
    (100, 15),
    (49, 0),   # just below 50
    (50, 10),
    (9, 0),
    (10,5)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30 ", 30),
    ("sAVe1", 1)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",      # missing E
    "SAVE0",      # out of range lower
    "SAVE51",     # out of range upper
    "save-5",
    "SAVEabc",
    "S AVE10",   # internal space
    ""          # empty
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_and_subtotal(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new_and_increase(self):
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 2}
        # add same item with same price
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):   # negative unit_price
            self.cart.add_item("orange", -2.0, 1)
        with pytest.raises(ValueError):   # zero quantity
            self.cart.add_item("orange", 2.0, 0)
        with pytest.raises(ValueError):   # quantity not int (float)
            self.cart.add_item("orange", 2.0, 2.5)
        # different price for same item
        self.cart.add_item("pear", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 4.0, 1)

    def test_remove_item_partial_and_total(self):
        self.cart.add_item("banana", 0.5, 10)   # 10 items
        self.cart.remove_item("banana", 3)
        assert self.cart.items() == {"banana": 7}
        self.cart.remove_item("banana", 7)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_remove_more_than_quantity(self):
        self.cart.add_item("grape", 2.0, 4)
        # remove more than current
        self.cart.remove_item("grape", 10)  # should delete item
        assert "grape" not in self.cart.items()

    def test_subtotal_bulk_discount(self):
        # Item 1: quantity 5 (no discount) price 20 => subtotal 100
        self.cart.add_item("itemA", 20, 5)
        # Item 2: quantity 12 -> 5% discount on 12*30=360 => 342
        self.cart.add_item("itemB", 30, 12)
        expected_subtotal = 100 + 342.0  # 442.0
        assert self.cart.subtotal() == expected_subtotal

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("toy", 20, 5)  # quantity=5 -> no discount: subtotal 100
        total_no_coupon = self.cart.total()
        assert total_no_coupon == 160.0  # shipping fee 60

        # with coupon 50% off
        total_with_coupon = self.cart.total(coupon="SAVE50")
        # subtotal after bulk (none) is 100; coupon 50% => 50; add shipping 60 -> 110
        assert total_with_coupon == 110.0

    def test_total_member_shipping(self):
        self.cart.add_item("lego", 30, 5)  # 150
        total_non_member = self.cart.total()
        assert total_non_member == 210.0
        total_member = self.cart.total(member=True)
        assert total_member == 180.0

    def test_total_invalid_coupon(self):
        self.cart.add_item("card", 10, 2)  # subtotal 20
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_items_is_copy(self):
        self.cart.add_item("book", 5, 3)
        items = self.cart.items()
        items["book"] = 100   # modify copy
        assert self.cart.items() == {"book": 3}
