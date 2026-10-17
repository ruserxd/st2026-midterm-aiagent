import pytest
import cart

# Test apply_discount
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,expected", [
    (100, 33.3333, round(100*(1-33.3333/100),2)),
    (50.5, 10, round(50.5*0.9,2)),
    (0, 0, 0.0),
])
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 10),           # negative price
    (100, -5),           # percent < 0
    (100, 105),          # percent > 100
])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),          # boundary expected value
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 5.5, "ten"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Test parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    (" save25 ", 25),   # whitespace should be ignored
    ("save1", 1),       # case-insensitive
    ("SAVE50", 50)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVEX",
    "",
    "abc10",
    "SAVE10X"
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # add_item tests
    def test_add_new_item(self):
        self.cart.add_item("apple", 1.5, quantity=3)
        assert self.cart.items() == {"apple": 3}
        assert self.cart.subtotal() == round(1.5 * 3, 2)

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 0.99, quantity=2)
        self.cart.add_item("banana", 0.99, quantity=4)
        assert self.cart.items() == {"banana": 6}
        assert self.cart.subtotal() == round(0.99 * 6, 2)

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("orange", 1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.0)

    @pytest.mark.parametrize("unit_price,quantity", [
        (-1, 1),
        (0.5, 0),
        (1.0, -3),
        (1.0, 1.5)
    ])
    def test_add_item_invalid_inputs(self, unit_price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", unit_price, quantity)

    # remove_item tests
    def test_remove_partial_quantity(self):
        self.cart.add_item("strawberry", 0.2, quantity=10)
        self.cart.remove_item("strawberry", quantity=4)
        assert self.cart.items() == {"strawberry": 6}

    def test_remove_entire_and_excess(self):
        self.cart.add_item("kiwi", 0.3, quantity=2)
        self.cart.remove_item("kiwi", quantity=5)
        assert "kiwi" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    # items copy test
    def test_items_returns_copy(self):
        self.cart.add_item("mango", 0.5, quantity=3)
        copy = self.cart.items()
        copy["mango"] = 10
        assert self.cart.items() == {"mango": 3}

    # subtotal tests
    def test_subtotal_with_bulk_discounts(self):
        self.cart.add_item("item1", 10.0, quantity=5)
        self.cart.add_item("item2", 20.0, quantity=12)
        self.cart.add_item("item3", 5.0, quantity=55)
        expected = (
            round(10.0 * 5, 2) +
            round(20.0 * 12 * 0.95, 2) +
            round(5.0 * 55 * 0.90, 2)
        )
        assert self.cart.subtotal() == expected

    def test_subtotal_empty_cart(self):
        assert cart.Cart().subtotal() == 0.0

    # total tests
    def test_total_no_items_and_coupon(self):
        c = cart.Cart()
        assert c.total(coupon="SAVE10") == 0.0
        assert c.total(member=True, coupon="SAVE10") == 0.0

    def test_total_with_shipping_and_membership(self):
        c = cart.Cart()
        c.add_item("pen", 20.0, quantity=10)
        expected_sub = round(20.0 * 10 * 0.95, 2)   # 190
        assert c.subtotal() == expected_sub

        # No coupon, non-member
        assert c.total(member=False) == round(expected_sub + 60, 2)

        # Coupon and member
        total_with_coupon_member = round((expected_sub * 0.90) + 30, 2)
        assert c.total(member=True, coupon="SAVE10") == total_with_coupon_member

    def test_total_free_shipping_after_coupon(self):
        # Subtotal below 1000 before discount
        c = cart.Cart()
        c.add_item("widget", 20.0, quantity=50)   # bulk discount percent should be 10%
        subtotal_before_coupon = round(20.0 * 50 * 0.90, 2)
        assert subtotal_before_coupon == 900.0
        # After coupon SAVE10
        total_after_coupon = round(subtotal_before_coupon * 0.90 + 60, 2)
        assert c.total(member=False, coupon="SAVE10") == total_after_coupon

        # Subtotal above 1000 after discount
        d = cart.Cart()
        d.add_item("gadget", 20.0, quantity=70)   # bulk discount percent 10%
        subtotal_d = round(20.0 * 70 * 0.90, 2)
        assert subtotal_d == 1260.0
        total_with_coupon_free_shipping = round(subtotal_d * 0.90, 2)
        assert d.total(member=False, coupon="SAVE10") == total_with_coupon_free_shipping

    def test_total_invalid_coupon_raises(self):
        c = cart.Cart()
        c.add_item("item", 1.0)
        with pytest.raises(ValueError):
            c.total(coupon="INVALIDCODE")
