import pytest
import cart

# --- helper for rounding consistency ---
# Note: spec says round to 2 decimals where needed.

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# errors for negative price or invalid percent
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected", [
    (9, 0),   # below 10
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# errors for non-positive quantity
@pytest.mark.parametrize("qty", [0, -5, -1.3])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe50  ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "savet", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# errors for negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initially_empty(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    # add_item behavior
    @pytest.mark.parametrize("name,price,qty", [
        ("apple", 1.5, 2),
        ("banana", 0.8, 5),
    ])
    def test_add_new_items(self, name, price, qty):
        self.c.add_item(name, price, qty)
        assert self.c.items()[name] == qty
        # subtotal should reflect bulk discount for quantity>=10? none here
        expected_subtotal = round(price * qty, 2)
        assert self.c.subtotal() == expected_subtotal

    def test_add_existing_item_same_price(self):
        self.c.add_item("apple", 1.0, 3)
        self.c.add_item("apple", 1.0, 4)
        assert self.c.items()["apple"] == 7
        assert self.c.subtotal() == round(1.0 * 7, 2)

    def test_add_existing_item_different_price(self):
        self.c.add_item("orange", 2.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 3.0, 2)

    # remove_item behavior
    def test_remove_partial_and_complete(self):
        self.c.add_item("apple", 1.0, 5)
        self.c.remove_item("apple", 2)
        assert self.c.items()["apple"] == 3
        self.c.remove_item("apple", 3)
        assert "apple" not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexist", 1)

    # subtotal discounts
    def test_subtotal_bulk_discount(self):
        # 12 apples at $10 each -> bulk discount 5%
        self.c.add_item("apple", 10.0, 12)
        expected = round(10.0 * 12 * (1 - cart.bulk_discount_percent(12)/100), 2)
        assert self.c.subtotal() == expected

    # total calculation with coupon and shipping
    def test_total_with_coupon_and_shipping(self):
        self.c.add_item("item", 200.0, 3)   # subtotal 600
        coupon = cart.parse_coupon("SAVE10")  # 10%
        after_discount = round(600 * (1 - 10/100), 2)
        shipping = cart.shipping_fee(after_discount, member=False)
        total_expected = round(after_discount + shipping, 2)
        assert self.c.total(coupon=coupon) == total_expected

    def test_total_member_no_coupon(self):
        self.c.add_item("item", 1200.0, 1)  # subtotal >1000 free shipping
        assert self.c.total(member=True) == round(1200.0, 2)

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0
