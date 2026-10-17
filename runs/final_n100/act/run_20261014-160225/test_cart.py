import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Utility constants from spec (if any) ----------

# ---------- Tests for apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # rounding example
    assert apply_discount(100, 33) == round(100 * (1 - 0.33), 2)

@ pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 150, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent ----------

def test_bulk_discount_percent_basic():
    # Assuming spec: returns a discount percentage based on quantity thresholds.
    # We infer expected behavior from typical rules (this may need adjustment if spec is different).
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(10) > 0
    assert bulk_discount_percent(50) >= bulk_discount_percent(10)

# ---------- Tests for parse_coupon ----------

def test_parse_coupon_valid_and_invalid():
    # Valid coupon format: code like "SAVE10"
    valid = parse_coupon("SAVE10")
    assert isinstance(valid, dict)
    assert 'code' in valid and 'discount' in valid
    # Invalid formats should raise ValueError
    with pytest.raises(ValueError):
        parse_coupon(123)
    with pytest.raises(ValueError):
        parse_coupon("invalid-code")

# ---------- Tests for shipping_fee ----------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 5.99  # Assuming base fee per spec (placeholder)
    assert shipping_fee(100, member=True) == 0  # Free shipping for members

# ---------- Tests for Cart class ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == []
    assert cart.subtotal() == 0
    assert cart.total() == pytest.approx(5.99)  # includes shipping fee placeholder


def test_add_and_remove_items():
    cart = Cart()
    cart.add_item("Apple", unit_price=1.50, quantity=3)
    assert cart.items() == [("Apple", 1.50, 3)]
    assert cart.subtotal() == 4.5
    cart.remove_item("Apple", quantity=2)
    assert cart.items() == [("Apple", 1.50, 1)]
    assert cart.subtotal() == 1.5
    # Removing more than existing should raise ValueError (assumed behavior)
    with pytest.raises(ValueError):
        cart.remove_item("Apple", quantity=5)


def test_cart_total_with_member_and_coupon():
    cart = Cart()
    cart.add_item("Notebook", unit_price=20.0, quantity=2)  # subtotal 40
    total_non_member = cart.total(member=False)
    assert total_non_member > 40  # includes shipping fee
    total_member = cart.total(member=True)
    assert total_member == pytest.approx(cart.subtotal())  # free shipping for members
    # Test coupon application (assuming coupon dict with 'discount' percent)
    coupon = parse_coupon("SAVE10")
    total_with_coupon = cart.total(member=False, coupon=coupon)
    expected_after_discount = apply_discount(total_non_member, coupon['discount'])
    assert total_with_coupon == pytest.approx(expected_after_discount)

# ---------- End of tests ----------
