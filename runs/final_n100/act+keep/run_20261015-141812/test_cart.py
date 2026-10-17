import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Discount functions ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -0.01])
@ pytest.mark.parametrize("percent", [10])
def test_apply_discount_negative_price(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@ pytest.mark.parametrize("price", [100])
@ pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Bulk discount ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Coupon parser ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@ pytest.mark.parametrize("code", ["", "NOTACODE", "SAve-5", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Shipping fee ----------

def test_shipping_fee():
    assert shipping_fee(1200) == 0
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(0) == 60
    assert shipping_fee(999, member=True) == 30
    assert shipping_fee(500, member=False) == 60

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_subtotal_and_total_non_members():
    cart = Cart()
    assert cart.subtotal() == 0.0
    assert cart.total(member=False) == 0.0

    # add items with various quantities to trigger bulk discounts
    cart.add_item("apple", unit_price=10, quantity=9)
    # no bulk discount
    assert cart.subtotal() == 90.0

    cart.add_item("banana", unit_price=5, quantity=10)  # 5% off banana
    expected = (90 + 5 * 10 * 0.95)  # 10 bananas with 5% bulk discount
    assert cart.subtotal() == round(expected, 2)

    # total without coupon, non-member shipping
    subtotal_after_bulk = cart.subtotal()
    expected_total = subtotal_after_bulk + shipping_fee(subtotal_after_bulk, member=False)
    assert cart.total(member=False) == round(expected_total, 2)


def test_cart_with_coupon_and_membership():
    cart = Cart()
    cart.add_item("widget", unit_price=200, quantity=10)  # 5% bulk discount
    subtotal_bulk = 200 * 10 * 0.95
    assert cart.subtotal() == round(subtotal_bulk, 2)

    # apply coupon SAVE20 (20%) then member shipping
    total_before_shipping = subtotal_bulk - (subtotal_bulk * 0.20)
    expected_total = total_before_shipping + shipping_fee(total_before_shipping, member=True)
    assert cart.total(member=True, coupon="SAVE20") == round(expected_total, 2)


def test_cart_invalid_coupon():
    cart = Cart()
    cart.add_item("test", 10, 1)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ---------- Edge case: empty cart shipping fee not charged ----------

def test_empty_cart_no_shipping():
    cart = Cart()
    assert cart.total(member=True) == 0.0
