import pytest
from cart import Cart, parse_coupon, apply_discount, shipping_fee

# Helper to get coupon percent from a valid code

def _coupon_percent(code: str) -> float:
    return parse_coupon(code)

class TestCartTotal:
    def test_empty_cart_total_zero(self):
        c = Cart()
        assert c.total() == 0, "Empty cart should cost nothing (no shipping)."

    def test_no_coupon_non_member(self):
        c = Cart()
        # add a single item with unit price 10 and quantity 3 => subtotal 30
        c.add_item("apple", 10.0, 3)
        sub = c.subtotal()
        exp_shipping = shipping_fee(sub, member=False)
        expected_total = round(sub + exp_shipping, 2)
        assert c.total() == expected_total

    def test_no_coupon_member(self):
        c = Cart()
        c.add_item("banana", 5.0, 4)  # subtotal 20
        sub = c.subtotal()
        exp_shipping = shipping_fee(sub, member=True)
        expected_total = round(sub + exp_shipping, 2)
        assert c.total(member=True) == expected_total

    def test_valid_coupon_reduces_subtotal_and_ships_on_discount(self):
        # Assuming there is a coupon "SAVE10" that gives 10% off
        valid_code = "SAVE10"
        percent = _coupon_percent(valid_code)
        assert percent == pytest.approx(10.0), f"Expected 10% for {valid_code}"

        c = Cart()
        c.add_item("widget", 20.0, 2)  # subtotal 40
        discounted_sub = apply_discount(c.subtotal(), percent)
        exp_shipping = shipping_fee(discounted_sub, member=False)
        expected_total = round(discounted_sub + exp_shipping, 2)
        assert c.total(coupon=valid_code) == expected_total

    def test_invalid_coupon_raises_value_error(self):
        c = Cart()
        c.add_item("item", 15.0, 1)
        with pytest.raises(ValueError):
            c.total(coupon="INVALIDCODE")
