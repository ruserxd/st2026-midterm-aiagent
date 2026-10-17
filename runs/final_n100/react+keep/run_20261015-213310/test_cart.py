import cart
import pytest

# Helper to format amounts consistently
from decimal import Decimal

# ---------- Coupon Parsing ----------

def test_parse_coupon_valid_and_invalid():
    assert cart.parse_coupon("10%OFF") == 10
    assert cart.parse_coupon(" 20 %   ") == 20
    # leading zeros allowed
    assert cart.parse_coupon("0010%") == 10

    with pytest.raises(ValueError):
        cart.parse_coupon("")
    with pytest.raises(ValueError):
        cart.parse_coupon("NOPE")
    with pytest.raises(ValueError):
        cart.parse_coupon("150%")   # percent > 100

# ---------- Bulk Discount ----------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(3) == 0
    assert cart.bulk_discount_percent(5) == 10
    assert cart.bulk_discount_percent(8) == 20
    assert cart.bulk_discount_percent(12) == 30

# ---------- Shipping Fee ----------

def test_shipping_fee_free_over_threshold():
    # subtotal >= 1000 -> free shipping
    assert cart.shipping_fee(1000, member=False) == 0
    assert cart.shipping_fee(1500.5, member=True) == 0


def test_shipping_fee_charged_for_non_members_and_members_under_threshold():
    # subtotal < 1000 and non-member -> 60
    assert cart.shipping_fee(999.99, member=False) == 60
    # member under threshold gets half
    assert cart.shipping_fee(500, member=True) == 30

    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# ---------- Cart Operations ----------

def test_cart_add_and_remove_items_and_subtotal():
    c = cart.Cart()
    # Initially empty
    assert c.subtotal() == 0
    # Add one item
    c.add_item("Widget", 10.00, quantity=3)
    assert c.items()["Widget"] == {"unit_price": 10.00, "quantity": 3}
    assert c.subtotal() == 30.00
    # Add same item again
    c.add_item("Widget", 10.00, quantity=2)
    assert c.items()["Widget"]["quantity"] == 5
    assert c.subtotal() == 50.00
    # Remove some quantity
    c.remove_item("Widget", quantity=1)
    assert c.items()["Widget"]["quantity"] == 4
    assert c.subtotal() == 40.00
    # Remove all
    c.remove_item("Widget", quantity=4)
    assert "Widget" not in c.items()
    assert c.subtotal() == 0

# ---------- Cart Total with Coupon and Shipping ----------

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    # Add items totaling $200
    c.add_item("Gadget", 50, quantity=4)
    # Subtotal should be 200
    assert c.subtotal() == 200.0
    # Without coupon or membership: shipping fee 60 -> total 260
    assert c.total(member=False) == 260.0
    # With member discount: shipping half -> total 230
    assert c.total(member=True) == 230.0
    # Add coupon 10% off
    assert c.total(coupon="10%OFF") == pytest.approx(200*0.9 + 60, rel=1e-6)
    # Combined member and coupon: shipping half of discounted subtotal
    assert c.total(member=True, coupon="10%OFF") == pytest.approx(200*0.9 + 30, rel=1e-6)

# ---------- Edge Cases: Empty Cart ----------

def test_empty_cart_total_and_subtotal():
    c = cart.Cart()
    assert c.subtotal() == 0
    # No shipping for empty cart
    assert c.total(member=False) == 0
    assert c.total(coupon="10%OFF") == 0
    assert c.total(member=True, coupon=None) == 0

# ---------- Coupon Validation in Cart.total ----------

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("Item", 100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
