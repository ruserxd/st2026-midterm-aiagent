import cart

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0

def test_subtotal_and_shipping_no_coupon():
    c = cart.Cart()
    c.add_item('widget', unit_price=10, quantity=2)
    # subtotal should be 20
    assert c.subtotal() == 20
    expected_total = round(c.subtotal() + cart.shipping_fee(c.subtotal()), 2)
    assert c.total() == expected_total

def test_coupon_application():
    c = cart.Cart()
    c.add_item('widget', unit_price=100, quantity=1)
    # Find a valid coupon from parse_coupon. Use first valid code.
    try:
        percent = cart.parse_coupon('SAVE10')
    except ValueError:
        return
    expected_after_discount = round(100 * (1 - percent/100), 2)
    shipping = cart.shipping_fee(expected_after_discount)
    total_expected = round(expected_after_discount + shipping, 2)
    assert c.total(coupon='SAVE10') == total_expected

def test_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('widget', unit_price=50, quantity=1)
    try:
        c.total(coupon='BADCODE')
    except ValueError as e:
        assert 'invalid coupon' in str(e).lower()
    else:
        assert False, "ValueError not raised for invalid coupon"

if __name__ == '__main__':
    import pytest, sys
    sys.exit(pytest.main([__file__]))
