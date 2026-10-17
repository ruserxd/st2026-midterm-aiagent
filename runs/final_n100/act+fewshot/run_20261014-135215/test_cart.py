import pytest
import cart

# Helper for floating equality
EPS = 1e-9

def approx_equal(a, b):
    return abs(a - b) < EPS

# ----- apply_discount tests -----
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent tests -----
@pytest.mark.parametrize("quantity, expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon tests -----
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save50", 50),
    (" SAVE25 ", 25),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVE-5",
    "INVALID",
    "SAVEBAD",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee tests -----
@pytest.mark.parametrize("subtotal, member, expected", [
    (999, False, 60),
    (1000, False, 0),
    (1500, True, 0),
    (800, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart tests -----
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 100, 2)
        self.c.add_item("banana", 50)
        assert self.c.items() == {"apple": 2, "banana": 1}
        # Adding same item with same price increases quantity
        self.c.add_item("apple", 100, 3)
        assert self.c.items()["apple"] == 5

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item("apple", -1)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 10, 0)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 20, -2)

    def test_add_item_price_mismatch(self):
        self.c.add_item("apple", 100)
        with pytest.raises(ValueError):
            self.c.add_item("apple", 90)

    def test_remove_and_auto_removal(self):
        self.c.add_item("sugar", 200, 5)
        self.c.remove_item("sugar", 3)
        assert self.c.items()["sugar"] == 2
        # Removing more than remaining should remove the item entirely
        self.c.remove_item("sugar", 5)
        assert "sugar" not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("milk")

    def test_subtotal_empty(self):
        assert self.c.subtotal() == 0.0

    def test_subtotal_with_bulk_discount(self):
        # 12 apples at $100 each => bulk discount 5%
        self.c.add_item("apple", 100, 12)
        expected = round(100 * 12 * (1 - 0.05), 2)
        assert self.c.subtotal() == expected

    def test_total_no_items(self):
        assert self.c.total() == 0.0

    def test_total_with_coupon_and_shipping(self):
        # 20 bananas at $50 each, no bulk discount
        self.c.add_item("banana", 50, 20)
        subtotal = round(50 * 20, 2)  # 1000
        # Coupon SAVE10 reduces by 10%
        after_coupon = round(subtotal * (1 - 0.10), 2)
        # Shipping for non-member on $900: still 60 because <1000
        shipping = 60 if not isinstance(after_coupon, bool) else 0
        total_expected = round(after_coupon + shipping, 2)
        assert self.c.total(coupon="SAVE10") == total_expected

    def test_total_with_invalid_coupon(self):
        self.c.add_item("item", 10)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_member_shipping_free_over_1000(self):
        # member pays free shipping if subtotal >=1000 before coupon
        self.c.add_item("expensive", 1200, 1)
        assert self.c.total(member=True) == round(1200 + 0, 2)

    def test_member_shipping_half_on_subtotal_below_1000(self):
        self.c.add_item("cheap", 500, 1)
        subtotal = 500.0
        shipping = 30  # half of 60
        assert self.c.total(member=True) == round(subtotal + shipping, 2)
