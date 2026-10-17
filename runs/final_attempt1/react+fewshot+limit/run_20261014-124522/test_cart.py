import pytest
import cart

# Test apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Invalid price and percent
@pytest.mark.parametrize("price,percent", [(-10, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent boundaries
@pytest.mark.parametrize("qty,percent", [
    (9, 0),      # below first threshold
    (10, 5),     # first threshold inclusive
    (49, 5),
    (50, 10),    # second threshold inclusive
    (99, 10),
    (100, 15),   # third threshold inclusive
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

# Negative or zero quantity
@pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Test parse_coupon case sensitivity and whitespace
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# Invalid coupon formats
@pytest.mark.parametrize("code", [
    "SAVE0",        # below min
    "SAVE51",       # above max
    "SAVEB10",      # wrong prefix
    "10SAVE",       # missing prefix
    "SAVEX5",       # non-numeric
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee logic
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Test Cart functionality
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new_and_increment(self):
        self.c.add_item("apple", 1.0, quantity=2)
        assert self.c.items() == {"apple": 2}
        # add more of same item with same price
        self.c.add_item("apple", 1.0, quantity=3)
        assert self.c.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        self.c.add_item("banana", 2.0, quantity=1)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 3.0, quantity=1)

    def test_remove_item_partial_and_complete(self):
        self.c.add_item("orange", 0.5, quantity=4)
        self.c.remove_item("orange", quantity=2)
        assert self.c.items() == {"orange": 2}
        self.c.remove_item("orange", quantity=2)  # should remove entirely
        assert self.c.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("pear", quantity=1)

    def test_subtotal_bulk_discount(self):
        # 5 apples: no bulk discount, subtotal = 5 * 0.9 = 4.5
        self.c.add_item("apple", 0.9, quantity=5)
        assert self.c.subtotal() == 4.5
        # 15 bananas: bulk discount 5%, unit price 1.0
        self.c.add_item("banana", 1.0, quantity=15)
        # banana subtotal: 1.0*15*0.95 = 14.25
        assert self.c.subtotal() == round(4.5 + 14.25, 2)

    def test_total_no_coupon(self):
        self.c.add_item("item", 10.0, quantity=3)  # no bulk discount (qty 3)
        total = self.c.total(member=False, coupon=None)
        expected_subtotal = round(30.0, 2)
        expected_shipping = cart.shipping_fee(expected_subtotal, member=False)
        assert total == round(expected_subtotal + expected_shipping, 2)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("item", 200.0, quantity=1)  # subtotal 200
        coupon_code = "SAVE10"
        total = self.c.total(member=True, coupon=coupon_code)
        discounted = cart.apply_discount(200.0, cart.parse_coupon(coupon_code))
        shipping = cart.shipping_fee(discounted, member=True)
        expected_total = round(discounted + shipping, 2)
        assert total == expected_total

    def test_total_empty_cart(self):
        assert self.c.total(member=False, coupon=None) == 0.0
