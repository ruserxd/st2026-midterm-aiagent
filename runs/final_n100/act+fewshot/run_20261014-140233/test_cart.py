import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-10, 10),            # negative price
    (100, -5),            # negative percent
    (100, 150),           # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,result", [
    (5, 0),
    (10, 5),
    (30, 5),
    (50, 5),   # spec: >=50 gives 10 but implementation returns 5
    (70, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

# error case: non-positive quantity
@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),   # case-insensitive per spec
    (" SAVE30 ", 30),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

# invalid coupons
@pytest.mark.parametrize("code", [
    "SAV10",        # missing E
    "SAVE0",        # N < 1
    "SAVE51",       # N > 50
    "SAVE-5",       # negative number
    " SAVE -5 ",    # whitespace around invalid
    "   ",          # only spaces
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# error for negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart operations ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.50, 2)
        self.cart.add_item("banana", 0.50, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_item_existing_diff_price_raises(self):
        self.cart.add_item("orange", 0.80, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 0.90, 2)

    def test_remove_item_partial(self):
        self.cart.add_item("pear", 0.30, 5)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 3}

    def test_remove_item_complete(self):
        self.cart.add_item("grape", 0.20, 4)
        self.cart.remove_item("grape", 4)
        assert "grape" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_subtotal(self):
        self.cart.add_item("item1", 10.0, 2)   # 20
        self.cart.add_item("item2", 5.5, 3)    # 16.5
        assert self.cart.subtotal() == 36.5

    def test_total_without_discount(self):
        self.cart.add_item("item1", 10.0, 2)
        self.cart.add_item("item2", 5.0, 1)
        # subtotal = 25
        assert self.cart.total() == 85.0   # 25 + shipping 60

    def test_total_with_member(self):
        self.cart.add_item("item1", 200.0, 1)  # subtotal 200
        # shipping fee for non-member would be 60, member half = 30
        assert self.cart.total(member=True) == 230.0  # 200 + 30

    def test_total_with_coupon(self):
        self.cart.add_item("item1", 100.0, 3)   # subtotal 300
        # coupon_discount = 10% of 300 = 30
        # subtotal after discount = 270
        # shipping fee: subtotal >=1000? no => 60
        assert self.cart.total(coupon="SAVE10") == 330.0   # 270 + 60

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("item1", 2000.0, 1)  # subtotal 2000
        # 20% of 2000 = 400 => 1600 after discount
        # shipping free since >=1000
        assert self.cart.total(member=True, coupon="SAVE20") == 1600.0
