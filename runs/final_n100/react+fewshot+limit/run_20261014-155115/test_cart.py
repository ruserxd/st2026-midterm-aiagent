import pytest
import cart

# Helper to compute expected bulk discount percent

def expected_bulk_discount(q):
    if q >= 100:
        return 15
    if q >= 50:
        return 10
    if q >= 10:
        return 5
    return 0

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# negative price or bad percent raise ValueError
@pytest.mark.parametrize("price,percent", [(-1,10),(50,-5),(50,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (1,0), (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0,-1,3.5,"a"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save50", 50),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# invalid coupons
@pytest.mark.parametrize("code", ["",
                                   "SAVE0",
                                   "SAVE51",
                                   "DISCOUNT10",
                                   "SA VE10",
                                   "  save-5  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0.0, False, 60),
    (999.99, True, 30),
    (1000.0, False, 0),
    (1200.0, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# negative subtotal
@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class operations ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple":3}
        # adding again increases qty
        self.cart.add_item("apple", 1.0, quantity=2)
        assert self.cart.items() == {"apple":5}

    def test_add_same_name_diff_price_raises(self):
        self.cart.add_item("banana", 0.5)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.6)

    def test_remove_and_items(self):
        self.cart.add_item("carrot", 0.2, quantity=4)
        self.cart.remove_item("carrot", quantity=1)
        assert self.cart.items() == {"carrot":3}
        self.cart.remove_item("carrot", quantity=3)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("durian")

    def test_subtotal_with_bulk_discount(self):
        # 12 apples at $1 each: bulk discount 5%
        self.cart.add_item("apple", 1.0, quantity=12)
        expected = round(12 * 1.0 * (1 - expected_bulk_discount(12)/100),2)
        assert self.cart.subtotal() == expected

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("apple", 10.0, quantity=3)  # no bulk discount
        subtotal = 30.0
        shipping = cart.shipping_fee(subtotal)
        assert self.cart.total() == round(subtotal + shipping,2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("book", 20.0, quantity=5)  # no bulk discount
        subtotal = 100.0
        after_coupon = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
        shipping = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping,2)
        assert self.cart.total(member=True, coupon="SAVE10") == expected_total

    def test_empty_cart_totals(self):
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0
