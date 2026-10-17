import pytest
import cart

# Helper for discount calculation

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == round2(result)

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
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

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEx", "SAVE0", "SAVE51", "NOTCOUPON", "1234" ,""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.00, 3)
        self.c.add_item("banana", 0.50, 2)
        assert self.c.items() == {"apple": 3, "banana": 2}

    def test_add_existing_same_price(self):
        self.c.add_item("apple", 1.00, 1)
        self.c.add_item("apple", 1.00, 4)
        assert self.c.items() == {"apple": 5}

    def test_add_existing_different_price_error(self):
        self.c.add_item("apple", 1.00, 1)
        with pytest.raises(ValueError):
            self.c.add_item("apple", 2.00, 1)

    def test_remove_item(self):
        self.c.add_item("apple", 1.00, 3)
        self.c.remove_item("apple", 2)
        assert self.c.items() == {"apple": 1}

    def test_remove_item_to_zero_removes(self):
        self.c.add_item("apple", 1.00, 2)
        self.c.remove_item("apple", 3)  # more than existing
        assert "apple" not in self.c.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("orange", 1)

    def test_subtotal_no_discounts(self):
        self.c.add_item("item", 10.00, 4)  # quantity <10 => no bulk discount
        assert round2(self.c.subtotal()) == 40.0

    def test_subtotal_with_bulk_discount(self):
        # quantity 12 => bulk discount 5%
        self.c.add_item("item", 20.00, 12)
        expected = 20.00 * 12 * (1 - 0.05)  # 240 * 0.95
        assert round2(self.c.subtotal()) == round2(expected)

    def test_subtotal_multiple_items(self):
        self.c.add_item("itemA", 5.00, 10)   # 5% discount
        self.c.add_item("itemB", 3.00, 50)   # 10% discount
        sub_a = 5.00 * 10 * 0.95
        sub_b = 3.00 * 50 * 0.90
        assert round2(self.c.subtotal()) == round2(sub_a + sub_b)

    def test_total_no_coupon_no_member(self):
        self.c.add_item("item", 10.00, 1)  # subtotal 10
        total = 10.00 + cart.shipping_fee(10.00)
        assert round2(self.c.total()) == round2(total)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("item", 2000.00, 1)  # subtotal 2000
        coupon_percent = cart.parse_coupon("SAVE10")  # 10%
        after_coupon = 2000 * (1 - coupon_percent / 100)
        shipping = cart.shipping_fee(after_coupon, member=True)
        expected = after_coupon + shipping
        assert round2(self.c.total(member=True, coupon="SAVE10")) == round2(expected)

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.c.add_item("item", 10.00, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")
