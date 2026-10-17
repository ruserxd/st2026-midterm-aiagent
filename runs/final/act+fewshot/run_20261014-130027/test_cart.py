import pytest
import cart

# Utility for floating comparison
EPS = 1e-9

def assert_close(a, b):
    assert abs(a - b) < EPS, f"{a} != {b}"   

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected", [
    (0, 0),  # boundary: positive int required, but function may treat 0 as <10 ->0
    (5, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    if qty <=0:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(qty)
    else:
        assert cart.bulk_discount_percent(qty) == expected

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "", "ABC10", "SAVE0", "SAVE51", "SAVEX", "SAVE -5",
    "  ", "save50x", "saVE15"
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0)
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initial_empty(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new(self):
        self.c.add_item("apple", 1.5, 3)
        assert self.c.items() == {"apple": 3}
        # subtotal should apply bulk discount for 3 -> no discount
        assert_close(self.c.subtotal(), 4.5)

    def test_add_same_item_increases_quantity_and_price_check(self):
        self.c.add_item("banana", 0.8, 2)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 1.0, 1)  # price mismatch
        # add same price to increase quantity
        self.c.add_item("banana", 0.8, 3)
        assert self.c.items() == {"banana":5}
        # bulk discount: qty=5 -> 0% => subtotal 4.0
        assert_close(self.c.subtotal(), 4.0)

    def test_remove_item_partial_and_full(self):
        self.c.add_item("cherry", 2.0, 4)
        self.c.remove_item("cherry", 2)
        assert self.c.items() == {"cherry":2}
        # remove more than present should drop to zero
        self.c.remove_item("cherry", 5)
        assert "cherry" not in self.c.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexist", 1)

    def test_total_without_coupon_and_member(self):
        self.c.add_item("item", 100, 10)  # bulk discount 5%
        # subtotal after discount: 100*10=1000 -> 5% => 950.0
        assert_close(self.c.subtotal(), 950.0)
        total = self.c.total()
        # shipping: subtotal<1000 => fee 60, not member
        expected_total = 950.0 + 60
        assert_close(total, expected_total)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("gift", 200, 5)  # no bulk discount
        # subtotal 1000
        # coupon SAVE10 => 10% off -> 900.0
        total = self.c.total(member=True, coupon="SAVE10")
        # shipping: after coupon 900<1000 => fee 30 member
        expected_total = 900.0 + 30
        assert_close(total, expected_total)

    def test_total_empty_no_shipping(self):
        assert self.c.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.c.add_item("foo", 10, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BAD")
