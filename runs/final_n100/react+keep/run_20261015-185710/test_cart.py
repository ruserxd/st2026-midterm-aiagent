import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# Helper to compare floating numbers within tolerance

def float_eq(a, b, eps=1e-9):
    return abs(a - b) < eps

## 1. Test apply_discount specifications

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 100 * 33% -> 67.0 after rounding
    assert apply_discount(100, 33) == 67.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-10, 20)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        apply_discount(100, -1)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        apply_discount(100, 101)

## 2. Test bulk_discount_percent specifications

def test_bulk_discount_no_discount():
    assert bulk_discount_percent(5) == 0


def test_bulk_discount_small_quantity():
    # Spec requires 10% for 50 units
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

## 3. Test shipping_fee specifications

def test_shipping_fee_free_over_1000():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0


def test_shipping_fee_full_for_non_member():
    assert shipping_fee(500, member=False) == 60
    assert shipping_fee(999.99, member=False) == 60


def test_shipping_fee_half_for_member():
    assert shipping_fee(500, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

## 4. Test parse_coupon specifications (case‑insensitive and whitespace)

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    # lower‑case code should still work per spec
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30


def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        parse_coupon("SAve0")   # less than 1
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # more than 50
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        parse_coupon(" ")

## 5. Test Cart subtotal calculation (including bulk discounts)

def test_cart_subtotal_basic():
    cart = Cart()
    cart.add_item("apple", unit_price=1.00, quantity=4)   # no discount
    assert cart.subtotal() == 4.0


def test_cart_subtotal_with_bulk_discount():
    cart = Cart()
    cart.add_item("widget", unit_price=10.00, quantity=12)  # qualifies for 5% bulk discount
    expected = apply_discount(120, 5)
    assert float_eq(cart.subtotal(), round(expected, 2))


def test_cart_subtotal_multiple_items_and_discounts():
    cart = Cart()
    cart.add_item("gadget", unit_price=50.00, quantity=55)  # 10% discount
    cart.add_item("thingamajig", unit_price=20.00, quantity=9)  # no bulk discount
    expected_gadgets = apply_discount(2750, 10)
    expected_others = 180
    assert float_eq(cart.subtotal(), round(expected_gadgets + expected_others, 2))


def test_cart_subtotal_empty_cart():
    cart = Cart()
    assert cart.subtotal() == 0.0

## 6. Test Cart.total calculation (with coupon and member discounts)

def test_cart_total_no_coupon_non_member():
    cart = Cart()
    cart.add_item("item", unit_price=20.00, quantity=1)
    # subtotal 20 - shipping fee 60 -> total 80
    assert cart.total(member=False) == 80.0


def test_cart_total_no_coupon_member():
    cart = Cart()
    cart.add_item("item", unit_price=20.00, quantity=1)
    # subtotal 20 - shipping fee 30 -> total 50
    assert cart.total(member=True) == 50.0


def test_cart_total_with_valid_coupon_and_member():
    cart = Cart()
    cart.add_item("expensive", unit_price=200.00, quantity=1)
    # subtotal 200 - apply coupon SAVE10 -> 180
    # shipping fee 60 (non‑member) but member pays half
    assert cart.total(member=True, coupon="SAVE10") == 210.0


def test_cart_total_coupon_rounding_and_shipping():
    cart = Cart()
    cart.add_item("item", unit_price=33.00, quantity=1)
    # subtotal 33 - apply SAVE5 -> 31.35
    # shipping fee 60 non‑member but member pays half
    assert float_eq(cart.total(member=True, coupon="SAVE5"), round(31.35 + 30, 2))


def test_cart_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("item", unit_price=10.00, quantity=1)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

## 7. Test Cart item manipulation and shipping on empty cart

def test_cart_empty_total_zero_no_shipping():
    cart = Cart()
    assert cart.total() == 0.0

# Adjusted to spec: items returns {name: quantity}

def test_cart_add_and_remove_items_spec_compliant():
    cart = Cart()
    cart.add_item("pen", unit_price=1.5, quantity=2)
    assert len(cart.items()) == 1
    cart.remove_item("pen", quantity=1)
    # should still have one item but quantity reduced to 1
    assert cart.items()["pen"] == 1
    cart.remove_item("pen", quantity=1)
    # now removed completely
    assert "pen" not in cart.items()

# End of tests
