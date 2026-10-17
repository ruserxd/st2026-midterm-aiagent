import cart
import pytest

# Test subtotal calculations

def test_subtotal_basic():
    c = cart.Cart()
    c.add_item('apple', unit_price=200, quantity=3)
    assert c.subtotal() == 600

# Test empty cart returns 0 total and no shipping

def test_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0

# Test shipping fee logic directly via helper function
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [ (500, False, cart.SHIPPING_BASE),
      (500, True, cart.SHIPPING_BASE/2),
      (1000, False, 0),
      (1200, True, 0) ] )
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Test total calculation with coupon and shipping for non-empty cart
@pytest.mark.parametrize(
    "items, coupon, member, expected",
    [ ([("item", 200, 5)], None, False, round(200*5 + cart.SHIPPING_BASE, 2)),
      ([("item", 300, 4)], 'DISCOUNT10', False, round((300*4)*0.9 + cart.SHIPPING_BASE, 2)),
      ([("item", 500, 3)], 'DISCOUNT20', True, round((500*3)*0.8 + cart.SHIPPING_BASE/2, 2)) ] )
def test_total_with_coupon_and_shipping(items, coupon, member, expected):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, unit_price=price, quantity=qty)
    assert c.total(member=member, coupon=coupon) == expected

# Test invalid coupon raises ValueError

def test_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('x', 100)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')
