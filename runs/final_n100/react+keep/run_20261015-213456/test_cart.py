import cart
import pytest

# Helper to compare floating point results rounded to 2 decimals

def round_two(x):
    return round(float(x), 2)

# Test subtotal calculation with multiple items and quantity

def test_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("apple", unit_price=100, quantity=3)   # 300
    c.add_item("banana", unit_price=150, quantity=2)  # 300
    assert round_two(c.subtotal()) == 600.00

# Test that an empty cart has subtotal 0 and total 0 (no shipping)

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0

# Test coupon discount logic: valid coupon applies correct percentage

def test_valid_coupon_discount_and_shipping():
    c = cart.Cart()
    c.add_item("item", unit_price=200, quantity=5)  # subtotal 1000
    # 20% coupon -> discounted amount 800
    total = c.total(coupon="SAVE20")
    expected = 800 + cart.shipping_fee(800)
    assert round_two(total) == round_two(expected)

# Shipping free for subtotal >= 1000 after discount

def test_free_shipping_after_discount():
    c = cart.Cart()
    c.add_item("item", unit_price=400, quantity=3)  # subtotal 1200
    total = c.total(coupon="SAVE5")  # 5% off => 1140 > 1000 free shipping
    expected = 1200 * 0.95
    assert round_two(total) == round_two(expected)

# Members pay half shipping when not free

def test_member_shipping_half():
    c = cart.Cart()
    c.add_item("item", unit_price=200, quantity=3)  # subtotal 600
    total_nonmember = c.total(member=False, coupon="SAVE10")
    discounted_subtotal = 600 * 0.9
    expected_nonmember = round_two(discounted_subtotal + cart.shipping_fee(discounted_subtotal))
    assert round_two(total_nonmember) == expected_nonmember
    total_member = c.total(member=True, coupon="SAVE10")
    shipping_half = cart.shipping_fee(discounted_subtotal)/2
    expected_member = round_two(discounted_subtotal + shipping_half)
    assert round_two(total_member) == expected_member

# Invalid coupon should raise ValueError

def test_invalid_coupon_raises():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Coupon parsing accepts whitespace and case-insensitivity

def test_coupon_whitespace_and_case():
    assert cart.parse_coupon("SAVE25") == 25
    assert cart.parse_coupon("  save10 ") == 10

# Shipping fee logic tests directly

def test_shipping_fee_logic():
    # Subtotal >=1000: free shipping
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.5) == 0
    # <1000: full fee
    assert cart.shipping_fee(999.99) == 60
    # Member half
    assert cart.shipping_fee(200, member=True) == 30
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Round to two decimals check for total rounding behaviour

def test_total_rounding():
    c = cart.Cart()
    # price that leads to a non-terminating decimal after discount and shipping
    c.add_item("expensive", unit_price=333, quantity=3)  # subtotal 999
    # coupon 1% discount
    total = c.total(coupon="SAVE01")
    # compute expected manually with rounding
    discounted = 999 * 0.99
    shipping = cart.shipping_fee(discounted)
    expected = round_two(discounted + shipping)
    assert round_two(total) == expected
