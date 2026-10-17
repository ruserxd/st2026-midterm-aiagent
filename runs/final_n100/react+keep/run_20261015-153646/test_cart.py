import cart
import pytest

# --------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

# Edge values and rounding

def test_apply_discount_rounding():
    # 1% of 33 is 0.33, so expect 32.67
    assert cart.apply_discount(33, 1) == pytest.approx(32.67)

# Error cases

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# --------- bulk_discount_percent ----------------------------

def test_bulk_discount_limits():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

# Error case

def test_bulk_discount_error():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)

# --------- parse_coupon -------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save20') == 20
    assert cart.parse_coupon('  SaVe30 ') == 30

# Invalid cases

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon('DISCOUNT10')
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE0')   # below min 1
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE51')  # above max 50

# --------- shipping_fee -------------------------------------

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(1200, member=False) == 0
    assert cart.shipping_fee(1000, member=True) == 0
    assert cart.shipping_fee(999.99, member=False) == 60
    assert cart.shipping_fee(50, member=True) == 30

# Error on negative subtotal

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# --------- Cart class ---------------------------------------

def test_cart_basic_add_and_subtotal():
    c = cart.Cart()
    c.add_item('apple', 3, quantity=2)   # $6 total
    c.add_item('banana', 1, quantity=5)  # $5 total
    # No bulk discount yet
    assert c.subtotal() == 11.0

# Bulk discount in subtotal

def test_cart_bulk_discount_subtotal():
    c = cart.Cart()
    c.add_item('widget', 10, quantity=50)
    # bulk discount 10% on line total 500 -> discounted price 450
    assert c.subtotal() == 450.0

# Total with coupon and shipping mismatch test (should expose bug)

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('book', 100, quantity=1)
    # subtotal 100, apply coupon SAVE10 -> 90, shipping fee on 100 is 60
    expected = round(90 + 60, 2)   # 150.0
    actual = c.total(coupon='SAVE10')
    assert actual == expected

# Total when member discounts (shipping half)

def test_cart_total_member_shipping_half():
    c = cart.Cart()
    c.add_item('item', 200, quantity=1)
    # subtotal 200, no coupon, shipping fee on 200 is 60
    expected = round(200 + 30, 2)  # member gets half shipping: 230.0
    assert c.total(member=True) == expected

# Empty cart total zero

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

# Removing items

def test_remove_item_behavior():
    c = cart.Cart()
    c.add_item('pencil', 1, quantity=5)
    c.remove_item('pencil', quantity=3)
    assert c.items()['pencil'] == 2
    # remove remaining
    c.remove_item('pencil', quantity=2)
    assert 'pencil' not in c.items()

# Error on removing non-existent item

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')
