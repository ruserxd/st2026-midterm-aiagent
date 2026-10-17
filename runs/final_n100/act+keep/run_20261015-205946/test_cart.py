import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- Helper function for floating point comparisons

def approx(value, expected):
    assert round(value, 2) == round(expected, 2), f"{value!r} != {expected!r}"

# Test apply_discount specifications
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result)

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [ -5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# Test bulk_discount_percent specifications
@pytest.mark.parametrize("quantity,expected", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# Test parse_coupon specifications
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",     # below min N
    "SAVE51",    # above max N
    "INVALID",
    "save-5",
    "10SAVE",
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Test shipping_fee specifications
@pytest.mark.parametrize("subtotal,expected", [
    (0, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_non_member(subtotal, expected):
    assert shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal,expected", [
    (0, 30),
    (500, 30),
    (999.99, 30),
])
def test_shipping_fee_member(subtotal, expected):
    assert shipping_fee(subtotal, member=True) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Test Cart class functionality

def test_cart_initially_empty():
    cart = Cart()
    assert cart.items() == []
    assert cart.subtotal() == 0
    # total on empty cart should be 0, no shipping
    assert cart.total() == 0.00

# Adding items and subtotal calculation

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=3)
    c.add_item("banana", unit_price=50)
    assert c.items() == [(
        "apple", 100, 3
    ), (
        "banana", 50, 1
    )]
    # subtotal = 3*100 + 1*50 = 350
    assert c.subtotal() == 350

# Removing items

def test_cart_remove():
    c = Cart()
    c.add_item("item", unit_price=20, quantity=5)
    c.remove_item("item", quantity=2)
    # remaining quantity should be 3
    assert c.items() == [("item", 20, 3)]
    c.remove_item("item", quantity=3)
    assert c.items() == []
    with pytest.raises(ValueError):
        c.remove_item("nonexistent")

# Bulk discount effect via coupon is not directly in Cart; test total logic

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    # Add items worth 2000, so shipping free if no coupon
    c.add_item("expensive", unit_price=500, quantity=4)  # subtotal 2000
    # No coupon -> total should be 2000 (no shipping)
    assert c.total() == pytest.approx(2000.00)

    # Add a small item to make subtotal below threshold
    c = Cart()
    c.add_item("cheap", unit_price=20, quantity=2)   # 40
    total_no_coupon = c.total(member=True)
    # shipping fee member: 30, so expected 70.0
    assert total_no_coupon == pytest.approx(70.00)

    # Coupon SAVE10 reduces 10% of subtotal 40 => 36 + shipping 30 = 66
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(66.00)

# Test that invalid coupon in total raises ValueError

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("test", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")

# Ensure total rounds to two decimals even for non-terminating floats

def test_cart_total_rounding():
    c = Cart()
    c.add_item("half", unit_price=0.3333, quantity=1)
    # subtotal 0.33... round? After rounding: 0.33
    expected = apply_discount(0.3333, 0) + shipping_fee(0.3333)
    assert round(c.total(), 2) == round(expected, 2)
