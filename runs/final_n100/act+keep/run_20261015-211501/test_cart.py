import pytest
import cart

# Helper for rounding
from decimal import Decimal, ROUND_HALF_UP

def round2(val):
    return float(Decimal(val).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# --------- apply_discount ---------------------------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert round2(cart.apply_discount(123.45, 7)) == round2(114.83)

@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --------- bulk_discount_percent --------------------------------------------

def test_bulk_discount_percent_ranges():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("   SaVe5") == 5

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVExx", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------- shipping_fee -----------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_total(self):
        assert self.c.total() == 0.0

    def test_add_and_subtotal(self):
        self.c.add_item("Apple", unit_price=2, quantity=3)
        self.c.add_item("Banana", unit_price=1.5, quantity=4)
        assert round2(self.c.subtotal()) == round2(2*3 + 1.5*4)

    def test_remove_item_partial_and_total(self):
        self.c.add_item("Apple", unit_price=2, quantity=5)
        self.c.remove_item("Apple", quantity=2)
        assert len(self.c.items()) == 1
        name, price, qty = next(iter(self.c.items()))
        assert name == "Apple"
        assert price == 2
        assert qty == 3
        # total without coupon/member
        expected_subtotal = 2 * 3
        shipping = cart.shipping_fee(expected_subtotal)
        assert round2(self.c.total()) == round2(expected_subtotal + shipping)

    def test_bulk_discount_application(self):
        # bulk discount applies to quantity of a single item
        self.c.add_item("Widget", unit_price=10, quantity=120)  # should get 15%
        discounted_unit = cart.apply_discount(10, cart.bulk_discount_percent(120))
        assert discounted_unit == 8.5
        subtotal = discounted_unit * 120
        shipping = cart.shipping_fee(subtotal)
        assert round2(self.c.total()) == round2(subtotal + shipping)

    def test_coupon_and_member_shipping(self):
        self.c.add_item("Gadget", unit_price=200, quantity=3)  # subtotal 600
        coupon_percent = cart.parse_coupon("SAVE10")  # 10% off
        discounted_subtotal = cart.apply_discount(600, coupon_percent)
        shipping_member = cart.shipping_fee(discounted_subtotal, member=True)
        expected_total = discounted_subtotal + shipping_member
        assert round2(self.c.total(member=True, coupon="SAVE10")) == round2(expected_total)

    def test_invalid_coupon_raises(self):
        self.c.add_item("Item", unit_price=50, quantity=1)
        with pytest.raises(ValueError):
            self.c.total(coupon="INVALID")

    def test_remove_nonexistent_item_no_error(self):
        # Removing an item not in cart should not raise
        self.c.remove_item("NonExistent", quantity=1)  # should simply ignore
        assert len(self.c.items()) == 0

# End of tests
