import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# ---------- Specification compliance tests ----------

def test_apply_discount_valid():
    # Normal discount
    assert apply_discount(200, 15) == 170.0
    # Edge percent values
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

# Errors for invalid price/percent

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-10, 10)
    with pytest.raises(ValueError):
        apply_discount(10, -5)
    with pytest.raises(ValueError):
        apply_discount(10, 105)


def test_bulk_discount_percent_levels():
    # Test the thresholds and discount percentages
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

# Errors for non-positive quantity

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)


def test_parse_coupon_valid_cases():
    # Case insensitive, whitespace tolerant
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE50 ") == 50
    assert parse_coupon("SaVe1") == 1

# Errors for invalid coupon strings

def test_parse_coupon_errors():
    with pytest.raises(ValueError):
        parse_coupon("INVALID")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")   # percent < 1
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # percent > 50
    with pytest.raises(ValueError):
        parse_coupon("SAVEXX")
    with pytest.raises(ValueError):
        parse_coupon(123)       # non-string type


def test_shipping_fee_rules():
    # Free shipping threshold
    assert shipping_fee(1000, member=False) == 0.0
    assert shipping_fee(1500, member=True) == 0.0
    # Regular fee for non-members
    assert shipping_fee(200, member=False) == 60.0
    # Regular fee half for members
    assert shipping_fee(300, member=True) == 30.0

# Errors for negative subtotal

def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10, member=False)

# ---------- Functional tests for Cart ----------

def create_basic_cart():
    c = Cart()
    c.add_item("Widget", unit_price=100.0, quantity=5)  # total 500 before discount
    return c


def test_cart_subtotal_single_discount():
    c = Cart()
    c.add_item("Gadget", unit_price=20.0, quantity=12)  # 240 subtotal with 5% bulk
    assert c.subtotal() == pytest.approx(228.0, rel=1e-9)


def test_cart_subtotal_multiple_items_and_discounts():
    c = Cart()
    c.add_item("ItemA", unit_price=50.0, quantity=10)   # 500 -> 5% discount => 475
    c.add_item("ItemB", unit_price=200.0, quantity=55)  # 11000 -> 10% => 9900
    assert pytest.approx(c.subtotal(), rel=1e-9) == 475 + 9900


def test_cart_total_no_coupon_non_member():
    c = create_basic_cart()
    # No coupon, subtotal after bulk is 500, shipping 60 -> total 560
    assert c.total(member=False) == pytest.approx(560.0, rel=1e-9)


def test_cart_total_with_coupon_and_member():
    c = create_basic_cart()
    # 5% coupon applied: 500 - 25 = 475; shipping 60 -> 30 for member
    assert c.total(member=True, coupon="SAVE5") == pytest.approx(505.0, rel=1e-9)


def test_cart_total_empty():
    c = Cart()
    assert c.total() == 0.0

# Verify that subtotal and total respect rounding to two decimals

def test_rounding_behavior():
    c = Cart()
    c.add_item("Item", unit_price=33.333, quantity=3)   # 99.999 -> round to 100.00 after bulk (no discount)
    assert c.subtotal() == pytest.approx(100.0, rel=1e-9)
    # Apply 10% coupon
    total = c.total(coupon="SAVE10")
    expected = apply_discount(100.0, 10) + shipping_fee(90.0, member=False)
    assert total == pytest.approx(expected, rel=1e-9)
