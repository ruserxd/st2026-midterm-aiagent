import pytest
import cart

# ---- apply_discount -----------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),        # example
    (100, 0, 100.0),         # no discount
    (100, 100, 0.0),         # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary checks for exceptions
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-1, 101, 150])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent -----------------------------------------------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 1.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",          # missing 'E'
    "SAVE0",          # out of range
    "SAVE51",         # >50
    "  ",            # only whitespace
    "BADCODE",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ---------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1.0, 2)
        self.cart.add_item("banana", 1.0, 3)
        assert self.cart.items() == {"banana": 5}

    def test_add_item_conflicting_price(self):
        self.cart.add_item("cherry", 0.8, 4)
        with pytest.raises(ValueError):
            self.cart.add_item("cherry", 1.0, 1)

    @pytest.mark.parametrize("quantity", [0, -2])
    def test_add_item_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("date", 3.0, quantity)

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("eggplant", 2.0, 5)
        self.cart.remove_item("eggplant", 2)
        assert self.cart.items() == {"eggplant": 3}
        self.cart.remove_item("eggplant", 3)  # should remove item
        assert "eggplant" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("fig", 1)

    def test_subtotal_simple(self):
        # 2 units @ 10 each, no bulk discount (qty=2 -> 0%)
        self.cart.add_item("grape", 10.0, 2)
        assert self.cart.subtotal() == 20.0

    def test_subtotal_with_bulk(self):
        # 12 units @ 5 each => bulk discount 5%
        self.cart.add_item("honey", 5.0, 12)
        expected = round(5.0 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_non_member(self):
        self.cart.add_item("icecream", 3.0, 4)  # qty=4 -> 0% bulk
        subtotal = 12.0
        total = cart.shipping_fee(subtotal)
        assert self.cart.total() == round(subtotal + total, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("juice", 10.0, 10)  # qty=10 -> 5% bulk
        subtotal = round(10.0 * 10 * (1 - 0.05), 2)
        coupon_percent = cart.parse_coupon("SAVE20")  # 20%
        after_coupon = subtotal * (1 - coupon_percent/100)
        shipping = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
