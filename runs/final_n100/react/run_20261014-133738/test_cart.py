import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Tests for apply_discount

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# Tests for bulk_discount_percent

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# Tests for parse_coupon

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon(' save20 ') == 20
    assert parse_coupon('SaVe5') == 5

@pytest.mark.parametrize("code", ['SAVE', 'save51', 'abc10', 'SAVE-5', 'SAVE0', 'SAVE100'])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Tests for Cart functionality

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item('apple', 100, 3)
    assert c.subtotal() == 300
    c.add_item('banana', 50)
    assert c.subtotal() == 350

@pytest.mark.parametrize("name, qty", [('apple', -1), ('', 2)])
def test_cart_add_invalid(name, qty):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item(name, 100, qty)

def test_cart_remove_and_items():
    c = Cart()
    c.add_item('item', 200, 5)
    c.remove_item('item', 2)
    assert c.items() == {'item': (200, 3)}
    c.remove_item('item', 3)
    assert c.items() == {}

@pytest.mark.parametrize("name, qty", [('nonexistent',1), ('item',4)])
def test_cart_remove_invalid(name, qty):
    c = Cart()
    c.add_item('item', 100, 2)
    with pytest.raises(ValueError):
        c.remove_item(name, qty)

# Test total calculation with coupon and shipping

def test_cart_total_no_coupon_member():
    c = Cart()
    c.add_item('x', 500, 1)
    assert c.total(member=True) == round(500 + 30,2)

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item('x', 1000, 1)
    # subtotal 1000 -\u003e free shipping after coupon too
    amount = apply_discount(1000, parse_coupon('SAVE10'))
    assert round(amount + shipping_fee(1000, False),2) == 900.0

# Empty cart total

def test_cart_total_empty():
    c = Cart()
    assert c.total() == 0
