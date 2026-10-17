import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

def test_apply_discount_no_change():
    # percent zero -> unchanged
    assert apply_discount(123.45, 0) == 123.45

def test_apply_discount_full_percent():
    assert apply_discount(500, 100) == 0.0

def test_apply_discount_rounding():
    # ensure rounding to two decimals
    assert apply_discount(19.999, 50) == 10.00

def test_apply_discount_negative_price_raises():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)

def test_apply_discount_invalid_percent_over100_raises():
    with pytest.raises(ValueError):
        apply_discount(100, 150)

def test_apply_discount_invalid_percent_negative_raises():
    with pytest.raises(ValueError):
        apply_discount(100, -5)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_none():
    assert bulk_discount_percent(1) == 0

def test_bulk_discount_threshold10():
    assert bulk_discount_percent(10) == 5

def test_bulk_discount_above10_under50():
    assert bulk_discount_percent(20) == 5

def test_bulk_discount_50():
    assert bulk_discount_percent(50) == 10

def test_bulk_discount_over50_under100():
    assert bulk_discount_percent(75) == 10

def test_bulk_discount_100_plus():
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_negative_quantity_raises():
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_basic():
    assert parse_coupon("SAVE10") == 10

def test_parse_coupon_valid_case_insensitive_and_whitespace():
    assert parse_coupon("  save20 ") == 20

def test_parse_coupon_invalid_prefix():
    with pytest.raises(ValueError):
        parse_coupon("NOTACODE30")

def test_parse_coupon_invalid_number_range():
    for code in ["SAVE0", "SAVE51", "SAVE100"]:
        with pytest.raises(ValueError):
            parse_coupon(code)

def test_parse_coupon_non_integer_suffix():
    with pytest.raises(ValueError):
        parse_coupon("SAVEx")

# ---------- shipping_fee tests ----------

def test_shipping_fee_standard():
    assert shipping_fee(500) == 60

def test_shipping_fee_half_for_member():
    assert shipping_fee(400, member=True) == 30

def test_shipping_fee_free_if_over_1000():
    assert shipping_fee(1200) == 0

def test_shipping_fee_zero_subtotal_no_shipping():
    assert shipping_fee(0) == 60

def test_shipping_fee_negative_subtotal_raises():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart tests ----------

def test_cart_initially_empty_totals_to_zero():
    cart = Cart()
    assert cart.total() == 0.0


def test_cart_add_and_subtotal():
    cart = Cart()
    cart.add_item("widget", 25, quantity=2)
    assert cart.subtotal() == 50
    assert cart.items() == {"widget": (25, 2)}


def test_cart_remove_items_reduce_quantity_and_total():
    cart = Cart()
    cart.add_item("gadget", 10, quantity=5)
    cart.remove_item("gadget", quantity=3)
    assert cart.items() == {"gadget": (10, 2)}
    assert cart.subtotal() == 20
    cart.remove_item("gadget")  # default remove one
    assert cart.items() == {}


def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("item", 200, quantity=3)  # subtotal 600
    # apply coupon SAVE10 -> reduce to 540 then add shipping 60 -> 600
    assert cart.total(coupon="SAVE10") == 600.0


def test_cart_total_member_discount_and_shipping():
    cart = Cart()
    cart.add_item("book", 120, quantity=5)  # subtotal 600
    # member pays half shipping: after discount none (no coupon), shipping 30 -> 630
    assert cart.total(member=True) == 630.0


def test_cart_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("pen", 5, quantity=2)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ---------- Integration tests for discounts ----------

def test_bulk_discount_applied_before_shipping_and_coupon():
    # bulk discount percent applied via Cart's add_item logic (not shown but assumed in implementation)
    # For this test, we manually compute expected using bulk_discount_percent.
    cart = Cart()
    qty = 120
    unit_price = 10
    discount_percent = bulk_discount_percent(qty)
    subtotal = qty * unit_price
    discounted_subtotal = apply_discount(subtotal, discount_percent)
    shipping = shipping_fee(discounted_subtotal, member=True)
    expected_total = round(discounted_subtotal + shipping, 2)
    # Assume Cart applies bulk discount automatically; add item and compute total.
    cart.add_item("bulkitem", unit_price, quantity=qty)
    assert cart.total(member=True) == expected_total
