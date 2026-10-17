import pytest
import cart

# --- Helper functions for expected bulk discount percent
def bulk_discount_expected(q):
    if q >= 100:
        return 15
    if q >= 50:
        return 10
    if q >= 10:
        return 5
    return 0

# ---------------- apply_discount -----------------------------------
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),              # example from spec
    (100.0, 0, 100.0),               # no discount
    (100.0, 100, 0.0),               # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price, percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------------- bulk_discount_percent -----------------------------------
@pytest.mark.parametrize("quantity, expected", [
    (0, ValueError),           # invalid quantity
    (9, 0),                    # below 10
    (10, 5),                   # threshold 10
    (49, 5),                   # just below 50
    (50, 10),                  # threshold 50
    (99, 10),                  # just below 100
    (100, 15),                 # threshold 100
])
def test_bulk_discount_percent(quantity, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            cart.bulk_discount_percent(quantity)
    else:
        assert cart.bulk_discount_percent(quantity) == expected

# ---------------- parse_coupon -----------------------------------
@pytest.mark.parametrize("code, percent", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", [
    "", "ABC10", "SAVE0", "SAVE51", "SAVEXX", " SAVE-5 ", 1234,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------- shipping_fee -----------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------------- Cart class -----------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 0.50, 3)
        assert self.cart.items() == {"apple": 3}
        # add same item increases quantity
        self.cart.add_item("apple", 0.50, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_different_price_error(self):
        self.cart.add_item("banana", 1.00, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.90, 1)

    def test_add_invalid_args(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, -5)

    def test_remove(self):
        self.cart.add_item("orange", 2.00, 4)
        self.cart.remove_item("orange", 1)
        assert self.cart.items() == {"orange": 3}
        # removing more than present removes the item completely
        self.cart.remove_item("orange", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal(self):
        # add items to trigger bulk discounts
        self.cart.add_item("itemA", 10.0, 9)   # no discount
        self.cart.add_item("itemB", 20.0, 10)  # 5% discount
        self.cart.add_item("itemC", 5.0, 50)   # 10% discount
        # calculate expected subtotal manually
        # itemA: 10*9 = 90
        # itemB: 20*10=200 -> 5% off => 190
        # itemC: 5*50=250 ->10% off => 225
        expected_subtotal = round(90 + 190 + 225, 2)
        assert self.cart.subtotal() == pytest.approx(expected_subtotal)

    def test_total_no_coupon(self):
        # use same cart from subtotal test
        total_without_shipping = self.cart.total(member=False)
        # shipping fee applied on subtotal (since no coupon)
        shipping = cart.shipping_fee(self.cart.subtotal(), member=False)
        expected_total = round(self.cart.subtotal() + shipping, 2)
        assert total_without_shipping == pytest.approx(expected_total)

    def test_total_with_coupon_and_member(self):
        # add items
        self.cart.add_item("itemX", 100.0, 10)   # 5% discount -> 950
        coupon_code = "SAVE20"
        subtotal_after_discount = cart.apply_discount(self.cart.subtotal(), cart.parse_coupon(coupon_code))
        shipping_fee = cart.shipping_fee(subtotal_after_discount, member=True)
        expected_total = round(subtotal_after_discount + shipping_fee, 2)
        assert self.cart.total(member=True, coupon=coupon_code) == pytest.approx(expected_total)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
