import cart
import math
import re
import pytest

# Helper for floating comparison

def approx(value, eps=1e-9):
    return lambda x: abs(x - value) < eps

# ------------- apply_discount ------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 123.456 with 10% discount -> 111.1104 round to 2 decimals
    assert cart.apply_discount(123.456, 10) == 111.11


def test_apply_discount_zero_percent():
    assert cart.apply_discount(50, 0) == 50.0


def test_apply_discount_full_percent():
    assert cart.apply_discount(75, 100) == 0.0


def test_apply_discount_negative_price_raises():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)


def test_apply_discount_invalid_percent_low_raises():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)


def test_apply_discount_invalid_percent_high_raises():
    with pytest.raises(ValueError):
        cart.apply_discount(100, 120)

# ------------- bulk_discount_percent ------------

def test_bulk_discount_percent_low_quantity():
    assert cart.bulk_discount_percent(9) == 0


def test_bulk_discount_percent_ten_units():
    assert cart.bulk_discount_percent(10) == 5


def test_bulk_discount_percent_fifty_units():
    assert cart.bulk_discount_percent(50) == 10


def test_bulk_discount_percent_hundred_units():
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_boundary():
    # just below thresholds
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(99) == 10


def test_bulk_discount_percent_invalid_nonpositive_raises():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-3)

# ------------- parse_coupon ------------

def test_parse_coupon_valid_simple():
    assert cart.parse_coupon("SAVE10") == 10


def test_parse_coupon_case_insensitive():
    assert cart.parse_coupon("save25") == 25


def test_parse_coupon_whitespace():
    assert cart.parse_coupon("   SAVE5  ") == 5


def test_parse_coupon_invalid_format_raises():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAV10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE55")  # >50

# ------------- shipping_fee ------------

def test_shipping_fee_free_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.75) == 0


def test_shipping_fee_standard_non_member():
    assert cart.shipping_fee(500) == 60


def test_shipping_fee_member_half():
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_fee_negative_subtotal_raises():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ------------- Cart class ------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # free shipping not applied until >1000? subtotal 0 -> shipping 60


def test_cart_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, quantity=2)
    c.add_item("banana", 0.75, quantity=3)
    assert c.items()["apple"] == (1.5, 2)
    assert c.items()["banana"] == (0.75, 3)
    # subtotal
    assert math.isclose(c.subtotal(), 1.5*2 + 0.75*3, abs_tol=1e-9)
    # remove one apple
    c.remove_item("apple", quantity=1)
    assert c.items()["apple"] == (1.5, 1)
    # removing more than present should remove item completely
    c.remove_item("banana", quantity=5)
    assert "banana" not in c.items()


def test_cart_total_with_discount_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=6)  # subtotal 1200
    # bulk discount for 6 units -> 5%
    discounted_unit = cart.apply_discount(200, cart.bulk_discount_percent(6))
    expected_subtotal = discounted_unit * 6
    # member shipping half of 60 =>30, but free above 1000 so shipping=0
    assert c.total(member=True) == expected_subtotal


def test_cart_total_with_coupon_and_non_member():
    c = cart.Cart()
    c.add_item("gadget", 100, quantity=1)
    # coupon SAVE20 -> 20%
    total = c.total(coupon="SAVE20")
    subtotal = 100
    discounted_subtotal = cart.apply_discount(subtotal, 20)
    shipping = cart.shipping_fee(discounted_subtotal, member=False)
    assert math.isclose(total, discounted_subtotal + shipping, abs_tol=1e-9)
