import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Discount functions ----------

@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),   # example from spec
        (100, 0, 100.0),      # no discount
        (50, 100, 0.0),       # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-6)

@ pytest.mark.parametrize(
    "price, percent",
    [
        (-10, 20),   # negative price
        (50, -5),    # invalid percent <0
        (30, 120),   # percent >100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Bulk discount function ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize(
    "quantity",
    [0, -1, -10],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Coupon parser ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SAVE30  ") == 30

@ pytest.mark.parametrize(
    "code",
    [
        "SAVEX",   # not numeric
        "" ,       # empty string
        "SAVE0",   # below 1
        "SAVE51",  # above 50
        "DISCOUNT10",  # wrong prefix
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Shipping fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60.0
    assert shipping_fee(100) == 60.0
    assert shipping_fee(999) == 60.0
    assert shipping_fee(1000) == 0.0
    # member half fee
    assert shipping_fee(50, member=True) == 30.0
    assert shipping_fee(500, member=True) == 30.0
    assert shipping_fee(1000, member=True) == 0.0

@ pytest.mark.parametrize(
    "subtotal",
    [-1, -10],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_basic_operations():
    c = Cart()
    # initially empty
    assert list(c.items()) == []
    assert c.subtotal() == 0.0
    
    # add items
    c.add_item("apple", 50, quantity=3)
    c.add_item("banana", 30, quantity=2)
    # adding same item increases quantity
    c.add_item("apple", 50, quantity=1)
    assert dict(c.items()) == {
        "apple": (50, 4),
        "banana": (30, 2),
    }
    # subtotal calculation
    assert c.subtotal() == 4*50 + 2*30

    # remove item partially
    c.remove_item("apple", quantity=2)
    assert dict(c.items()) == {"apple": (50, 2), "banana": (30, 2)}
    # removing more than present removes the item entirely
    c.remove_item("banana", quantity=5)
    assert dict(c.items()) == {"apple": (50, 2)}

    # total with discounts: no member or coupon
    expected_total = c.subtotal() + shipping_fee(c.subtotal(), member=False)
    assert c.total(member=False) == pytest.approx(expected_total, rel=1e-6)

    # total with member discount on shipping
    expected_member_total = c.subtotal() + shipping_fee(c.subtotal(), member=True)
    assert c.total(member=True) == pytest.approx(expected_member_total, rel=1e-6)

    # coupon discount applied after subtotal but before shipping
    coupon_percent = 20
    discounted_subtotal = apply_discount(c.subtotal(), coupon_percent)
    expected_coupon_total = (
        discounted_subtotal + shipping_fee(discounted_subtotal, member=False)
    )
    assert c.total(member=False, coupon=coupon_percent) == pytest.approx(
        expected_coupon_total, rel=1e-6
    )

    # invalid coupon raises ValueError
    with pytest.raises(ValueError):
        c.total(coupon=-5)

    # bulk discount applied automatically per item quantity when calculating total
    # create cart with 15 units of one product to get 5% bulk discount
    big_cart = Cart()
    big_cart.add_item("widget", 200, quantity=15)  # subtotal 3000
    # Bulk discount: 5% off unit price before coupon/shipping
    discounted_unit = apply_discount(200, 5)
    expected_bulk_total = 15 * discounted_unit
    total_with_bulk = big_cart.total()
    assert total_with_bulk == pytest.approx(expected_bulk_total + shipping_fee(expected_bulk_total), rel=1e-6)

# ---------- Edge cases for cart totals ----------

def test_cart_total_edge_cases():
    c = Cart()
    # Empty cart: subtotal 0, shipping fee should be applied based on subtotal 0 (60 for non-member)
    assert c.total(member=False) == pytest.approx(60.0, rel=1e-6)
    assert c.total(member=True) == pytest.approx(30.0, rel=1e-6)

# The following tests ensure that coupon and member flags behave independently.
def test_coupon_and_member_combination():
    c = Cart()
    c.add_item("gadget", 100, quantity=1)
    subtotal = c.subtotal()  # 100
    # Apply a 10% coupon (non-member)
    total_with_coupon = c.total(coupon=10)
    expected_coupon_total = apply_discount(subtotal, 10) + shipping_fee(apply_discount(subtotal, 10), member=False)
    assert total_with_coupon == pytest.approx(expected_coupon_total, rel=1e-6)

    # Apply same coupon as a member (shipping fee halved)
    total_with_coupon_member = c.total(member=True, coupon=10)
    expected_coupon_member_total = (
        apply_discount(subtotal, 10) + shipping_fee(apply_discount(subtotal, 10), member=True)
    )
    assert total_with_coupon_member == pytest.approx(expected_coupon_member_total, rel=1e-6)

# Test bulk discount logic is correctly used within Cart.total

def test_bulk_discount_in_cart_total():
    c = Cart()
    # 20 items of same product: should get 15% bulk discount on unit price
    c.add_item("thing", 50, quantity=20)
    discounted_unit_price = apply_discount(50, 15)  # 42.5
    expected_subtotal = 20 * discounted_unit_price
    total_without_coupon_member = c.total(member=False)
    assert total_without_coupon_member == pytest.approx(
        expected_subtotal + shipping_fee(expected_subtotal, member=False),
        rel=1e-6,
    )

# End of tests.
