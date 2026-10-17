import pytest
import cart

# Helper: round to two decimal places
round2 = lambda x: round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == round2(result)

@pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (100, -5),  # negative percent
    (100, 105), # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (1,0), (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10",10),
    ("save20",20),
    ("  SaVe5 ",5),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAVEX",   # non-integer suffix
    "SAVE0",   # below range
    "SAVE51",  # above range
    "10SAVE",  # wrong order
    "" ,
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, 3)
        assert self.cart.items() == {"apple":3}
        # bulk discount: 10 units -> 5% so no discount
        assert self.cart.subtotal() == round2(1.5*3)

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.8, 2)
        self.cart.add_item("banana", 0.8, 3)
        assert self.cart.items()["banana"] == 5
        # no bulk discount applied (quantity<10)
        assert self.cart.subtotal() == round2(0.8*5)

    def test_add_item_existing_diff_price(self):
        self.cart.add_item("orange", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.2, 1)

    @pytest.mark.parametrize("price,quantity", [(-5,1), (10,-3)])
    def test_add_invalid(self, price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("test", price, quantity)

    def test_remove_item_partial(self):
        self.cart.add_item("mango", 2.0, 5)
        self.cart.remove_item("mango", 3)
        assert self.cart.items()["mango"] == 2
        assert self.cart.subtotal() == round2(2.0*2)

    def test_remove_item_exact(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 4)
        assert "pear" not in self.cart.items()
        assert self.cart.subtotal() == 0

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist")

    def test_total_with_coupon_and_shipping(self):
        # Add items to exceed bulk discount thresholds
        self.cart.add_item("bread", 2.0, 12)   # 5% bulk discount
        self.cart.add_item("milk", 1.5, 50)   # 10% bulk discount
        subtotal = round2(2.0*12*(1-0.05) + 1.5*50*(1-0.10))
        assert self.cart.subtotal() == subtotal
        coupon_discount = cart.parse_coupon("SAVE20")
        after_coupon = round2(subtotal * (1 - coupon_discount/100))
        shipping = cart.shipping_fee(after_coupon)
        total_expected = round2(after_coupon + shipping)
        assert self.cart.total(coupon="SAVE20") == total_expected

    def test_total_no_items(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
