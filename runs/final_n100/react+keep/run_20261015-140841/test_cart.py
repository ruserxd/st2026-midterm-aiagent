import pytest
from cart import Cart, parse_coupon, shipping_fee, FREE_SHIPPING_THRESHOLD, SHIPPING_BASE

# Helper: create a cart with single item

def make_cart(unit_price, quantity=1):
    c = Cart()
    c.add_item("item", unit_price, quantity)
    return c

# ---------- Coupon parsing tests (spec) ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("  SaVe50") == 50


def test_parse_coupon_invalid_prefix_and_whitespace():
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        parse_coupon("SAVENOTNUMBER")


def test_parse_coupon_out_of_range():
    for percent in (-5, 0, 51, 100):
        code = f"SAVE{percent}"
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- Shipping fee tests (spec) ----------

def test_shipping_fee_non_member():
    assert shipping_fee(200) == 60
    assert shipping_fee(999.99) == 60


def test_shipping_fee_member_half_rate():
    assert shipping_fee(200, member=True) == 30


def test_shipping_fee_free_threshold():
    assert shipping_fee(FREE_SHIPPING_THRESHOLD) == 0
    assert shipping_fee(FREE_SHIPPING_THRESHOLD + 1) == 0

# ---------- Cart.total logic tests (spec) ----------

def test_cart_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0

@pytest.mark.parametrize("subtotal, coupon_percent, expected", [
    # no coupon
    (200, None, 260.0),  # subtotal + 60 shipping
    # with valid coupon <50% and not free shipping
    (300, "SAVE10", 330.0),  # 300-30=270; +60=330
])

def test_cart_total_subtotal_and_coupon(subtotal, coupon_percent, expected):
    c = make_cart(100, 2)  # subtotal 200
    if subtotal == 300:
        c.add_item("extra", 100)
    amount = c.total(coupon=coupon_percent)
    assert amount == expected

# Test that coupon is applied before shipping and rounding occurs

def test_cart_total_rounding_and_shipping_order():
    # subtotal 199, no coupon -> 199+60=259 rounded to 2 decimals remains 259.0
    c = make_cart(199)
    assert c.total() == 259.0

# Test invalid coupon raises ValueError

def test_cart_total_invalid_coupon_raises():
    c = make_cart(100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Test that shipping fee uses subtotal AFTER coupon discount (as per spec)

def test_shipping_fee_applied_after_coupon():
    # Subtotal 1200, free shipping threshold 1000 -> should be 0
    c = make_cart(600, 2)  # subtotal 1200
    assert c.total(coupon="SAVE10") == 1200.0

# Test member flag correctly halves shipping

def test_member_ships_half_fee():
    c = make_cart(100)
    assert c.total(member=True) == 130.0
