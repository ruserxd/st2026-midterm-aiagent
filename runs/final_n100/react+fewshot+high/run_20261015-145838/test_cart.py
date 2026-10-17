import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (10.00, 5, 9.5),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

def test_apply_discount_bounds():
    # price zero
    assert cart.apply_discount(0, 50) == 0.0
    # percent zero and full
    assert cart.apply_discount(50, 0) == 50.0
    assert cart.apply_discount(50, 100) == 0.0

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 150)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,percent", [
    (1, 0), (9, 0),
    (10, 5), (49, 5),
    (50, 10), (99, 10),
    (100, 15), (150, 15)
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("   SAVE50  ", 50),
    ("SaVe01", 1)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

def test_parse_coupon_invalid():
    invalid_codes = [
        "SAV10",
        "SAVE0",
        "SAVE51",
        "",
        "   ",
        "SAVE-5",
        "SAVE ten",
        "DISCOUNT10"
    ]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

def test_parse_coupon_leading_zero():
    assert cart.parse_coupon("SAVE05") == 5

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,fee", [
    (1000.00, False, 0),
    (999.99, False, 60),
    (500.00, True, 30)
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

def test_shipping_fee_zero():
    assert cart.shipping_fee(0) == 60

def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple": 3}
        self.cart.add_item("apple", 1.0, quantity=2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("banana", 0.5)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.75)

    def test_add_item_invalid_args(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0, quantity=-3)

    def test_remove_item(self):
        self.cart.add_item("pear", 2.0, quantity=5)
        self.cart.remove_item("pear", quantity=2)
        assert self.cart.items() == {"pear": 3}
        self.cart.remove_item("pear", quantity=5)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango")

    def test_subtotal_empty_and_with_discounts(self):
        assert self.cart.subtotal() == 0.0
        self.cart.add_item("item1", 10.0, quantity=3)
        assert self.cart.subtotal() == 30.0
        self.cart.add_item("item2", 20.0, quantity=12)  # bulk discount 5%
        expected_sub = 30.0 + cart.apply_discount(20.0 * 12, 5)
        assert self.cart.subtotal() == round(expected_sub, 2)

    def test_total_no_coupon(self):
        self.cart.add_item("widget", 50.0, quantity=2)  # subtotal 100
        expected = cart.apply_discount(100.0, 0) + 60
        assert self.cart.total() == round(expected, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("gadget", 200.0, quantity=3)  # subtotal 600
        coupon_percent = cart.parse_coupon("SAVE20")
        after_coupon = cart.apply_discount(600.0, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total

    def test_total_coupon_invalid(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_free_shipping_after_coupon(self):
        self.cart.add_item("expensive", 500.0, quantity=3)  # subtotal 1500
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = cart.apply_discount(1500.0, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon, member=False)
        total_expected = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_cross_threshold_non_member(self):
        self.cart.add_item("expensive", 500.0, quantity=3)  # subtotal 1500
        coupon_percent = cart.parse_coupon("SAVE50")
        after_coupon = cart.apply_discount(1500.0, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon, member=False)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(coupon="SAVE50") == expected_total

    def test_total_cross_threshold_member(self):
        self.cart.add_item("expensive", 500.0, quantity=3)  # subtotal 1500
        coupon_percent = cart.parse_coupon("SAVE50")
        after_coupon = cart.apply_discount(1500.0, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(member=True, coupon="SAVE50") == expected_total

    def test_total_exact_threshold_non_member(self):
        self.cart.add_item("expensive", 500.0, quantity=4)  # subtotal 2000
        coupon_percent = cart.parse_coupon("SAVE50")
        after_coupon = cart.apply_discount(2000.0, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon, member=False)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(coupon="SAVE50") == expected_total

    def test_total_exact_threshold_member(self):
        self.cart.add_item("expensive", 500.0, quantity=4)  # subtotal 2000
        coupon_percent = cart.parse_coupon("SAVE50")
        after_coupon = cart.apply_discount(2000.0, coupon_percent)
        shipping_fee = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(member=True, coupon="SAVE50") == expected_total

    def test_subtotal_rounding(self):
        self.cart.add_item("round", 10.555, quantity=1)  # no bulk discount
        assert self.cart.subtotal() == round(10.555, 2)

    def test_subtotal_multiple_items_rounding(self):
        self.cart.add_item("item1", 10.456, quantity=1)
        self.cart.add_item("item2", 20.123, quantity=1)
        expected = round(10.456 + 20.123, 2)
        assert self.cart.subtotal() == expected

# Additional function-level test
def test_apply_discount_rounding():
    # Test rounding when result has more than two decimal places
    assert cart.apply_discount(10.456, 5) == 9.93
