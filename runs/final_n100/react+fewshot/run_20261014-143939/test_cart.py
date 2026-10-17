import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),        # example from spec
    (100, 0, 100.0),         # no discount
    (50, 100, 0.0),          # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-1, 10),                # negative price
    (100, -5),               # percent < 0
    (100, 105),              # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),      # below 10
    (10, 5),     # exactly 10
    (49, 5),     # just below 50
    (50, 10),    # exactly 50
    (99, 10),    # just below 100
    (100, 15),   # exactly 100
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error cases: non-positive quantity
@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_error(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),   # case-insensitive
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# error cases: invalid format or percent out of range
@pytest.mark.parametrize("code", [
    "SAV10",          # missing E
    "SAVE0",          # below 1
    "SAVE51",         # above 50
    "12345",          # no SAVE
    "",               # empty
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,fee", [
    (1000, False, 0),   # free at 1000
    (999.99, False, 60),
    (500, True, 30),     # half for member
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# error case: negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_subtotal_and_total(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 100, 2)
        self.cart.add_item("banana", 50, 1)
        # adding same item increases quantity
        self.cart.add_item("apple", 100, 3)
        items = self.cart.items()
        assert items["apple"] == 5
        assert items["banana"] == 1

    def test_add_item_invalid_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -10, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 10, 0)

    def test_add_item_mismatched_unit_price(self):
        self.cart.add_item("pear", 30, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 25, 2)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("tomato", 20, 4)
        self.cart.remove_item("tomato", 2)  # quantity should be 2 now
        assert self.cart.items()["tomato"] == 2
        self.cart.remove_item("tomato", 2)  # remove all, item gone
        assert "tomato" not in self.cart.items()

    def test_remove_nonexistent_item(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_with_bulk_discount(self):
        # 12 apples, unit price 10 -> bulk discount 5%
        self.cart.add_item("apple", 10, 12)
        expected = 10 * 12 * (1 - 0.05)  # 120 * 0.95
        assert round(self.cart.subtotal(), 2) == round(expected, 2)

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("item", 200, 5)   # 5 items -> no bulk discount
        subtotal = 200 * 5  # 1000
        # coupon SAVE10 reduces by 10%
        total_before_shipping = subtotal * (1 - 0.10)
        # shipping free because amount >= 1000? Actually shipping fee computed on subtotal after coupon: if subtotal>=1000 shipping is free.
        expected_total = round(total_before_shipping, 2)  # no shipping
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_with_member_and_small_order(self):
        self.cart.add_item("item", 50, 1)
        subtotal = 50
        total_after_coupon = subtotal  # no coupon
        # shipping fee: subtotal < 1000 -> 60, member pays half => 30
        expected_total = round(subtotal + 30, 2)
        assert self.cart.total(member=True) == expected_total
