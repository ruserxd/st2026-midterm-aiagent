import pytest
from cart import Cart, shipping_fee, parse_coupon, FREE_SHIPPING_THRESHOLD, SHIPPING_BASE

# helper to create a cart with some items

def make_cart(items):
    c = Cart()
    for name, unit, qty in items:
        c.add_item(name, unit, qty)
    return c

# tests for parse_coupon spec
@ pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe30  ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@ pytest.mark.parametrize("code", [
    "", "SAVEX", "SAVE0", "SAVE51", "foo10", "SAVE-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests
@ pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1000.01, False, SHIPPING_BASE),
    (999.99, True, SHIPPING_BASE/2),
    (50, False, SHIPPING_BASE),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [ -1, -100 ])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart total tests
@pytest.fixture
def cart():
    return make_cart([
        ("apple", 100.0, 5),   # no discount
        ("banana", 200.0, 12), # bulk discount applies if defined
    ])

# Assume bulk_discount_percent gives 10% for quantity >=10
# We'll test subtotal independently

def test_subtotal(cart):
    expected = round(100.0*5 + 2400*0.9,2)
    assert cart.subtotal() == expected

def test_total_no_coupon(cart):
    amount = cart.subtotal()
    total_expected = round(amount + shipping_fee(amount), 2)
    assert cart.total() == total_expected

def test_total_with_valid_coupon(cart):
    subtotal = cart.subtotal()
    coupon_amount = apply_discount(subtotal, parse_coupon("SAVE10"))
    expected = round(coupon_amount + shipping_fee(coupon_amount), 2)
    assert cart.total(coupon="SAVE10") == expected

# invalid coupon raises ValueError in total
@ pytest.mark.parametrize("coupon", ["BADCODE", "", "save0"])
def test_total_invalid_coupon(cart, coupon):
    with pytest.raises(ValueError):
        cart.total(coupon=coupon)

# empty cart returns 0
def test_empty_cart():
    c = Cart()
    assert c.total() == 0
    assert c.total(coupon="SAVE10") == 0

# shipping fee uses subtotal after coupon, not before
@ pytest.mark.parametrize("subtotal,coupon", [
    (2000, None), # free shipping
    (1200, "SAVE10"),
])
def test_shipping_after_coupon(subtotal, coupon):
    c = Cart()
    c.add_item("expensive", subtotal, 1)
    amount_before = c.subtotal()
    if coupon:
        discounted = apply_discount(amount_before, parse_coupon(coupon))
        expected_total = round(discounted + shipping_fee(discounted),2)
    else:
        expected_total = round(subtotal + shipping_fee(subtotal),2)
    assert c.total(coupon=coupon) == expected_total
