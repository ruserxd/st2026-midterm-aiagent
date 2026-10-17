import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent

# Helper to create a cart with items

def make_cart(items):
    c = Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "", "SAVExx", "SAVE0", "SAVE51", "XYZ10", "save-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (1, 0), (5, 2), (10, 3), (20, 4), (50, 5),
])
def test_bulk_discount(qty, expected):
    assert bulk_discount_percent(qty) == expected

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# Tests for Cart.subtotal
@pytest.mark.parametrize("items,total", [
    ([], 0.00),
    ([('A', 10, 1)], 10.00),
    ([('B', 20, 5)], 20*5*(1-0.02)),
])
def test_cart_subtotal(items, total):
    c = make_cart(items)
    assert round(c.subtotal(), 2) == round(total, 2)

# Tests for Cart.total without coupon or member
@pytest.mark.parametrize("items,total", [
    ([], 0.00),
    ([('A', 200, 1)], 260.00), # 200 + 60 shipping
])
def test_cart_total_basic(items, total):
    c = make_cart(items)
    assert round(c.total(), 2) == round(total, 2)

# Tests for Cart.total with coupon and member
@pytest.mark.parametrize("items,coupon,member,total", [
    ([('A', 1000, 1)], 'SAVE10', False, 900.00), # subtotal 1000, discount 10%, no shipping
    ([('B', 200, 1)], 'SAVE20', True, 190.00), # subtotal 200-40=160 + 30 shipping
])
def test_cart_total_with_coupon(items,coupon,member,total):
    c = make_cart(items)
    assert round(c.total(member=member, coupon=coupon), 2) == round(total, 2)
