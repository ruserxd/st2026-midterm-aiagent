import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 33% discount on $10 = 6.7
    result = cart.apply_discount(10, 33)
    assert result == pytest.approx(6.7)

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent('10')

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save30') == 30
    assert cart.parse_coupon('   SaVe5  ') == 5
    assert cart.parse_coupon('SAVE1') == 1
    assert cart.parse_coupon('SAVE50') == 50

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVEX')
    with pytest.raises(ValueError):
        cart.parse_coupon('10SAVE')
    with pytest.raises(ValueError):
        cart.parse_coupon('')
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE0')
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE60')

def test_shipping_fee():
    # subtotal >=1000 = free
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # below threshold, non-member
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500) == 60
    # member discount
    assert cart.shipping_fee(500, member=True) == 30
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

def test_cart_add_and_subtotal():
    c = cart.Cart()
    c.add_item('apple', 2.5)
    assert c.subtotal() == 2.5
    c.add_item('banana', 1.0, quantity=3)
    assert c.subtotal() == 2.5 + 1.0 * 3

def test_cart_add_existing_same_price():
    c = cart.Cart()
    c.add_item('apple', 2.5, quantity=2)
    c.add_item('apple', 2.5, quantity=3)
    # subtotal should be 5 items at 2.5 each
    assert c.subtotal() == 5 * 2.5

def test_cart_add_existing_different_price():
    c = cart.Cart()
    c.add_item('apple', 2.5)
    with pytest.raises(ValueError):
        c.add_item('apple', 3.0)

def test_cart_remove_partial_and_full():
    c = cart.Cart()
    c.add_item('orange', 1.5, quantity=4)
    c.remove_item('orange', quantity=1)
    # remaining 3
    assert c.subtotal() == 3 * 1.5
    c.remove_item('orange', quantity=3)  # removes item entirely
    assert c.subtotal() == 0

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

def test_cart_add_invalid_parameters():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('bad', -1, quantity=1)
    with pytest.raises(ValueError):
        c.add_item('bad', 1, quantity=0)
    with pytest.raises(ValueError):
        c.add_item('bad', 1, quantity=-3)

# New tests

def test_cart_items_dict():
    c = cart.Cart()
    c.add_item('apple', 1.0, quantity=2)
    c.add_item('banana', 0.5, quantity=3)
    assert c.items() == {'apple': 2, 'banana': 3}

def test_total_no_coupon_or_member_small_subtotal():
    c = cart.Cart()
    c.add_item('item1', 200)   # subtotal 200
    expected = round(200 + 60, 2)
    assert c.total() == expected

def test_total_with_coupon_and_member_shipping():
    c = cart.Cart()
    c.add_item('item1', 800)   # subtotal 800
    # apply coupon SAVE10 => 10% discount on subtotal: 720
    # shipping fee for 720 is 60, member -> 30
    expected = round(720 + 30, 2)
    assert c.total(member=True, coupon='SAVE10') == expected

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.0

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('item', 100)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')

def test_shipping_free_over_threshold():
    c = cart.Cart()
    c.add_item('expensive', 1200)  # subtotal > 1000
    expected = round(1200 + 0, 2)
    assert c.total() == expected
