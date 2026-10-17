import pytest
import cart

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # Price * quantity with bulk discount calculation
    assert cart.apply_discount(19.99*12, 5) == round(239.88 * 0.95, 2)

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)
    assert cart.apply_discount(0, 50) == 0
    assert cart.apply_discount(10, 100) == 0.0

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(7) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(15) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(55) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-3)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(5.5)

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon('SAVE10') == 10
    # Case-insensitive: should be accepted per spec
    assert cart.parse_coupon('save10') == 10
    # Whitespace trimming
    assert cart.parse_coupon('  SAVE50 ') == 50

def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        cart.parse_coupon(123)
    with pytest.raises(ValueError):
        cart.parse_coupon('DISCOUNT10')
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE0')
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE51')

def test_shipping_fee():
    # Below threshold
    assert cart.shipping_fee(200) == 60
    assert cart.shipping_fee(200, member=True) == 30
    # Exactly at threshold (1000)
    assert cart.shipping_fee(1000) == 0
    # Negative subtotal raises error
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

def test_add_item():
    c = cart.Cart()
    c.add_item('apple', 10, quantity=2)
    assert c.items() == {'apple': 2}
    # Adding same item increments quantity
    c.add_item('apple', 10, quantity=3)
    assert c.items() == {'apple': 5}
    # Different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item('apple', 12, quantity=1)
    # Negative unit price or zero/negative quantity raise ValueError
    with pytest.raises(ValueError):
        c.add_item('banana', -1, quantity=1)
    with pytest.raises(ValueError):
        c.add_item('banana', 5, quantity=0)

def test_remove_item():
    c = cart.Cart()
    c.add_item('item', 5, quantity=2)
    # Removing part of quantity
    c.remove_item('item', 1)
    assert c.items() == {'item': 1}
    # Removing remaining quantity should remove the item entirely per spec
    c.remove_item('item', 1)
    assert 'item' not in c.items()
    # Removing nonexistent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item('nonexistent', 1)

def test_items_returns_copy():
    c = cart.Cart()
    c.add_item('x', 3, quantity=4)
    d = c.items()
    d['x'] = 0
    assert c.items()['x'] == 4

def test_subtotal_calculation():
    c = cart.Cart()
    # Item 1: 19.99 * 12 => bulk discount 5%
    c.add_item('widget', 19.99, quantity=12)
    # Item 2: 5.00 * 3 => no discount
    c.add_item('gadget', 5.0, quantity=3)
    expected = round(round(239.88*0.95, 2) + 15.0, 2)   # 242.89
    assert c.subtotal() == expected

def test_total_no_coupon_and_member():
    c = cart.Cart()
    c.add_item('widget', 19.99, quantity=12)
    c.add_item('gadget', 5.0, quantity=3)
    subtotal = c.subtotal()
    # Non-member
    assert c.total(member=False) == round(subtotal + cart.shipping_fee(subtotal), 2)
    # Member
    assert c.total(member=True) == round(subtotal + cart.shipping_fee(subtotal, member=True), 2)

def test_total_with_coupon():
    c = cart.Cart()
    c.add_item('widget', 19.99, quantity=12)
    c.add_item('gadget', 5.0, quantity=3)
    subtotal = c.subtotal()
    coupon_percent = 10
    discounted = round(subtotal * (100 - coupon_percent) / 100, 2)
    expected_non_member = round(discounted + cart.shipping_fee(discounted), 2)
    expected_member = round(discounted + cart.shipping_fee(discounted, member=True), 2)
    assert c.total(member=False, coupon='SAVE10') == expected_non_member
    assert c.total(member=True, coupon='SAVE10') == expected_member

def test_total_coupon_shipping_edge():
    # Cart with subtotal >=1000
    c = cart.Cart()
    c.add_item('expensive', 1500, quantity=1)
    # Coupon 50% to reduce below threshold
    assert c.total(member=False, coupon='SAVE50') == 810.00
    assert c.total(member=True, coupon='SAVE50') == 780.00

def test_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
