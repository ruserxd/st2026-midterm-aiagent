import cart
import pytest

def round2(val):
    return round(float(val), 2)

# ----- Shipping fee tests -----

def test_shipping_fee_free_and_standard():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60


def test_member_ships_half():
    assert cart.shipping_fee(200, member=True) == 30

# ----- Coupon parsing tests -----

def test_parse_coupon_valid_and_invalid():
    assert cart.parse_coupon("SAVE10") == 10
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")

# ----- Cart basic operations -----

def test_cart_add_remove_items_and_total_no_discount_shipping():
    c = cart.Cart()
    c.add_item("item", 20.0, quantity=2)
    assert c.items() == {"item": 2}
    # subtotal should be 40.00
    assert round2(c.subtotal()) == 40.00
    # total with no coupon: shipping fee 60 => 100
    assert round2(c.total()) == 100.00

# ----- Total calculation with coupon and shipping after discount -----

def test_total_with_coupon_and_shipping_after_discount():
    c = cart.Cart()
    c.add_item("product", 200.0, quantity=5)  # subtotal 1000
    total = c.total(coupon="SAVE10")
    # After 10% discount: 900; shipping fee 60 -> 960
    assert round2(total) == 960.00

# ----- Test that invalid coupon raises in total -----

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 10, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
