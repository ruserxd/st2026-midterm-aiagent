import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount -----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent -----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon -----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25 ", 25),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["",
                                  "SAVE0",
                                  "SAVE51",
                                  "SAVEXX",
                                  "INVALID10",
                                  "  ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class -----------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_empty_cart_total(self):
        assert self.cart.total() == 0.00

    def test_add_and_subtotal(self):
        self.cart.add_item("apple", 5, quantity=3)
        assert self.cart.subtotal() == 15.0

    def test_remove_items(self):
        self.cart.add_item("banana", 2, quantity=10)
        self.cart.remove_item("banana", quantity=4)
        # remaining 6 bananas at $2 each = $12 subtotal
        assert self.cart.subtotal() == 12.0

    def test_bulk_discount_applied_via_total(self):
        # buying 100 apples gives bulk discount percent 15% on total
        self.cart.add_item("apple", 10, quantity=100)
        expected_sub = 1000.0  # before discount
        assert self.cart.subtotal() == expected_sub
        # coupon None, member False
        # total after discount: 15% off => 850, shipping free because subtotal>=1000? actually subtotal was 1000 >? equals 1000 so shipping free.
        assert self.cart.total() == 850.00

    def test_coupon_and_shipping(self):
        self.cart.add_item("widget", 30, quantity=2)  # subtotal 60
        # coupon SAVE20 gives 20% off => 48, shipping fee for non-member is 60 because subtotal after discount <1000.
        assert self.cart.total(coupon="SAVE20") == 108.00

    def test_member_shipping_half(self):
        self.cart.add_item("gadget", 25, quantity=4)  # subtotal 100
        # no coupon, member True => shipping fee half of 60 =30
        assert self.cart.total(member=True) == 130.00

    def test_invalid_coupon_in_total(self):
        self.cart.add_item("item", 10)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
