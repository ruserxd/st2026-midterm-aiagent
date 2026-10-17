import cart
import pytest

# Test apply_discount

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # check rounding
    assert cart.apply_discount(100.555, 10) == round(100.555 * 0.9, 2)

@ pytest.mark.parametrize("price,percent", [(-1,10), (50,-5), (50,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Test parse_coupon

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save20') == 20
    assert cart.parse_coupon(' SAVE30 ') == 30

@ pytest.mark.parametrize("code", ['ABC', 'SAVExx', 'SAVE51', '', ' save0'])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee

def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1500, member=False) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Minimal Cart tests to confirm API consistency

def test_cart_api():
    c = cart.Cart()
    # items should be empty list initially
    assert c.items() == []
    # add item
    c.add_item('apple', 100, quantity=2)
    assert len(c.items()) == 1
    assert c.subtotal() == 200
    # total without member or coupon
    assert c.total(member=False) == cart.shipping_fee(200) + 200
    # remove item
    c.remove_item('apple', quantity=1)
    assert c.subtotal() == 100

# Ensure Cart respects bulk discount via parse_coupon usage? Not specified
