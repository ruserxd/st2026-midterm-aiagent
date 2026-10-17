import pytest
from cart import parse_coupon, apply_discount, bulk_discount_percent, shipping_fee, Cart

# ----- Tests for parse_coupon -----

def test_parse_coupon_valid_codes():
    # Test case-insensitivity and whitespace trimming
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe50 ") == 50


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")  # does not start with SAVE
    with pytest.raises(ValueError):
        parse_coupon("SAVEabc")  # non-numeric
    with pytest.raises(ValueError):
        parse_coupon("SAVEX")   # missing number


def test_parse_coupon_percent_range():
    # Percent less than 1 or greater than 50 should raise
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")

# ----- Tests for apply_discount -----

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_edge_cases():
    # percent 0 and 100 should be allowed
    assert apply_discount(123.45, 0) == 123.45
    assert apply_discount(99.99, 100) == 0.0


def test_apply_discount_invalid_inputs():
    with pytest.raises(ValueError):
        apply_discount(-10, 20)
    with pytest.raises(ValueError):
        apply_discount(50, -5)
    with pytest.raises(ValueError):
        apply_discount(50, 120)

# ----- Tests for bulk_discount_percent -----

def test_bulk_discount_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        bulk_discount_percent("10")

# ----- Tests for shipping_fee -----

def test_shipping_fee_free_for_qualified():
    # subtotal >= 1000 yields zero fee regardless of membership
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500, member=True) == 0


def test_shipping_fee_non_member_and_member():
    # Base fee is 60 for non-members below threshold
    assert shipping_fee(500) == 60
    # Members get half the fee below threshold
    assert shipping_fee(300, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ----- Tests for Cart.total logic and integration -----

def test_cart_total_basic_no_discount_or_member():
    cart = Cart()
    cart.add_item("widget", 20, quantity=2)  # subtotal 40
    assert cart.subtotal() == 40
    # No coupon: 40 + shipping 60 => 100
    assert cart.total() == 100.0


def test_cart_total_with_coupon_and_member():
    cart = Cart()
    cart.add_item("gadget", 500)
    # subtotal 500, apply 10% discount -> 450
    # shipping fee for member on discounted amount: 30
    # total should be 480.0
    assert cart.total(member=True, coupon="SAVE10") == 480.0


def test_cart_total_empty():
    cart = Cart()
    assert cart.subtotal() == 0
    assert cart.total() == 0
    assert cart.total(coupon="SAVE10") == 0  # coupon should be ignored when empty

# ----- Test that total uses discounted subtotal for shipping fee ----

def test_cart_total_shipping_fee_on_discounted_amount():
    cart = Cart()
    cart.add_item("expensive", 1200)
    # subtotal >= 1000 so free shipping regardless of coupon
    assert cart.total(coupon="SAVE10") == apply_discount(1200, 10)  # no shipping

# ----- Test that Cart.total raises error for invalid coupon string type -----

def test_cart_total_invalid_coupon_type():
    cart = Cart()
    cart.add_item("thing", 50)
    with pytest.raises(ValueError):
        cart.total(coupon=123)  # not a string
