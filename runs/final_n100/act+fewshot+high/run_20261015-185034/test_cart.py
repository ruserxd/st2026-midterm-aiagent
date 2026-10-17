import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price, percent, expected", [
    (100, 33, 67.0),   # 100 * 0.67 = 67.0
    (99.99, 10, 89.991),  # 99.99*0.90=89.991 -> round to 2 decimals = 89.99
])

def test_apply_discount_rounding(price, percent, expected):
    assert round(cart.apply_discount(price, percent), 2) == round(expected, 2)

@ pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])

def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_ranges():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -1])

def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save20') == 20
    assert cart.parse_coupon(' SAVE30 ') == 30

@ pytest.mark.parametrize("code", ["SAVEXX", "", "SAVE0", "SAVE51", "A10", "10SAVE"]) 

def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal, member, expected", [
    (500, False, 60),
    (500, True, 30),
])

def test_shipping_fee_member(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-1, -100])

def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert isinstance(self.cart.items(), dict)
        assert len(self.cart.items()) == 0
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    # add_item tests
    def test_add_new_item(self):
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 3}
        assert self.cart.subtotal() == round(100 * 3, 2)  # no bulk discount yet

    def test_add_existing_increases_quantity_and_unit_price_must_match(self):
        self.cart.add_item("banana", 50, 5)
        # same unit price
        self.cart.add_item("banana", 50, 2)
        assert self.cart.items() == {"banana": 7}

    def test_add_existing_unit_price_mismatch(self):
        self.cart.add_item("orange", 80, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 90, 1)

    @ pytest.mark.parametrize("name, unit_price, quantity", [
        ("pear", -10, 2),
        ("grape", 20, 0),
        ("melon", 30, -5),
    ])
    def test_add_item_invalid_inputs(self, name, unit_price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item(name, unit_price, quantity)

    # remove_item tests
    def test_remove_existing_reduce_quantity(self):
        self.cart.add_item("kiwi", 70, 4)
        self.cart.remove_item("kiwi", 2)
        assert self.cart.items() == {"kiwi": 2}

    def test_remove_item_leads_to_removal_when_zero_or_less(self):
        self.cart.add_item("mango", 90, 3)
        self.cart.remove_item("mango", 3)  # quantity becomes zero
        assert "mango" not in self.cart.items()
        # removing more than remaining should also remove entirely
        self.cart.add_item("mango", 90, 2)
        self.cart.remove_item("mango", 5)
        assert "mango" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pineapple", 1)

    # items method returns a copy
    def test_items_is_copy(self):
        self.cart.add_item("peach", 60, 2)
        d = self.cart.items()
        d["peach"] = 99
        assert self.cart.items()["peach"] == 2  # original unaffected

    # subtotal calculation with bulk discounts
    def test_subtotal_with_bulk_discounts(self):
        # apple: 10 units, discount 5% -> unit price 95
        self.cart.add_item("apple", 100, 10)
        # banana: 101 units, discount 15% -> unit price 85
        self.cart.add_item("banana", 100, 101)  # same unit price 100 for discount test
        expected = round(95 * 10 + 85 * 101, 2)
        assert self.cart.subtotal() == expected

    # total calculation with coupon and shipping
    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("widget", 200, 5)  # no bulk discount -> 1000
        subtotal = self.cart.subtotal()
        assert subtotal == round(200 * 5, 2)
        # apply coupon SAVE10 (10%) and non-member shipping
        total = self.cart.total(coupon="SAVE10", member=False)
        expected_after_coupon = round(subtotal * 0.90, 2)
        expected_shipping = cart.shipping_fee(expected_after_coupon, False)
        assert total == round(expected_after_coupon + expected_shipping, 2)

    def test_total_member_half_shipping(self):
        self.cart.add_item("widget", 200, 5)
        subtotal = self.cart.subtotal()
        total = self.cart.total(member=True)  # no coupon
        expected_shipping = cart.shipping_fee(subtotal, True)
        assert total == round(subtotal + expected_shipping, 2)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
