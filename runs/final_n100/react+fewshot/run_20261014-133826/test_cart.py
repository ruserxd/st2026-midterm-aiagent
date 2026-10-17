import pytest
import cart

# ---- apply_discount tests ----
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full discount
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary and error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [ -1, -5, 101, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent tests ----
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error for non-positive quantity
@pytest.mark.parametrize("quantity", [0, -5, -1])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon tests ----
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons: wrong prefix, out-of-range N, non-integer, empty
@pytest.mark.parametrize("code", [
    "SAVE0",        # below 1
    "SAVE51",       # above 50
    "SAVEXX",      # non-numeric
    "DISCOUNT10",   # wrong prefix
    "",             # empty
    "   ",          # whitespace only
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee tests ----
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1500, True, 0),   # free for any subtotal >=1000
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# error: negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart tests ----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1.5, 2)
        self.cart.add_item("banana", 1.5, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_same_name_different_price_raises(self):
        self.cart.add_item("orange", 0.8)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, 2)

    def test_remove_item_partial(self):
        self.cart.add_item("mango", 3.0, 5)
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {"mango": 3}

    def test_remove_item_full_removal(self):
        self.cart.add_item("peach", 4.0, 2)
        self.cart.remove_item("peach", 2)
        assert "peach" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("kiwi", 1)

    def test_subtotal_calculation(self):
        self.cart.add_item("bread", 2.5, 4)   # 10.0
        self.cart.add_item("milk", 1.25, 2)   # 2.5
        assert self.cart.subtotal() == 12.5

    def test_total_with_member_and_coupon(self):
        # items: apple 2.0x3 =6; banana 1.0x10=10 -> subtotal 16
        self.cart.add_item("apple", 2.0, 3)
        self.cart.add_item("banana", 1.0, 10)
        # coupon SAVE5 gives 5% off on total before shipping
        total = self.cart.total(member=True, coupon="SAVE5")
        # subtotal=16; coupon 5% -> 15.20; member shipping half 30->15; but subtotal<1000 so fee 30, half 15
        assert total == pytest.approx(30.20)

    def test_total_without_member_or_coupon(self):
        self.cart.add_item("item", 10.0, 1)
        assert self.cart.total() == 10.0
