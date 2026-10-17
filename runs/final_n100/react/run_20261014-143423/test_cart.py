import re
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_valid_cases():
    # basic percentage reduction
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0
    # rounding to two decimals
    assert apply_discount(99.999, 10) == round(99.999 * 0.9, 2)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)


def test_apply_discount_invalid_percent():
    for p in [-5, 101]:
        with pytest.raises(ValueError):
            apply_discount(100, p)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15


def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("  SaVe50  ") == 50


def test_parse_coupon_invalid_format():
    for code in ["SAVEx", "SAVE51", "ABCD10", "", "123", "SAVE0"]:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

def test_shipping_fee_free_and_reduced():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    # non-member fee
    assert shipping_fee(999) == 60
    # member half
    assert shipping_fee(500, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart class -----------------------------------------------------

def test_cart_initial_state_and_items():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0


def test_cart_add_and_remove_item_basic():
    c = Cart()
    c.add_item("apple", 50, quantity=2)
    assert c.items()["apple"] == (50, 2)
    assert c.subtotal() == 100

    c.remove_item("apple")
    # one quantity removed
    assert c.items()["apple"] == (50, 1)
    assert c.subtotal() == 50

    c.remove_item("apple", quantity=2)  # remove remaining and extra
    assert "apple" not in c.items()


def test_cart_total_with_bulk_and_shipping():
    cart = Cart()
    cart.add_item("widget", 100, quantity=12)
    # Bulk discount for 12 units: 5%
    discounted_price = apply_discount(100, bulk_discount_percent(12))
    assert cart.subtotal() == round(discounted_price * 12, 2)

    # non-member total includes shipping fee
    expected_total = cart.subtotal() + shipping_fee(cart.subtotal())
    assert cart.total(member=False) == pytest.approx(expected_total, rel=1e-9)

    # member gets half shipping
    expected_member_total = cart.subtotal() + shipping_fee(cart.subtotal(), member=True)
    assert cart.total(member=True) == pytest.approx(expected_member_total, rel=1e-9)


def test_cart_total_with_coupon_and_bulk_discount():
    c = Cart()
    c.add_item("tshirt", 200, quantity=10)
    # Bulk discount percent for 10 units is 5%
    bulk_disc = bulk_discount_percent(10)
    discounted_unit_price = apply_discount(200, bulk_disc)

    subtotal_before_coupon = round(discounted_unit_price * 10, 2)

    coupon_code = "SAVE20"
    coupon_discount = parse_coupon(coupon_code)  # 20%

    total_after_coupon = apply_discount(subtotal_before_coupon, coupon_discount)
    shipping = shipping_fee(total_after_coupon)
    expected_total = round(total_after_coupon + shipping, 2)

    assert c.total(member=False, coupon=coupon_code) == pytest.approx(expected_total, rel=1e-9)

# ---------- Edge cases for Cart -------------------------------------------

def test_cart_invalid_inputs():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("item", -10)
    with pytest.raises(ValueError):
        cart.remove_item("nonexistent")  # removing non-existing should raise
