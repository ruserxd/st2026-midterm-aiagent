import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- utility helpers ----------

def _assert_almost_equal(a, b, eps=1e-6):
    assert abs(a - b) < eps

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    # 15% off of 200 => 170.0
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent, expected",
    [ (100, 0, 100.0),
      (100, 100, 0.0),
      (99.99, 10, 90.0),
    ] )
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [ -1, -100 ])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -5, 105, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_bounds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, -20])
def test_bulk_discount_negative_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_basic():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SaVe5 ") == 5

@ pytest.mark.parametrize("code", ["SAVEBAD", "100", "SAVE0", "SAVE51", "BADCODE"])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(800, member=True) == 30

@ pytest.mark.parametrize("subtotal", [ -1, -50])
def test_shipping_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_initial_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", 100, quantity=3)
    c.add_item("banana", 50, quantity=2)
    # subtotal = 3*100 + 2*50 = 400
    assert c.subtotal() == 400.0

def test_cart_remove_and_subtotal():
    c = Cart()
    c.add_item("item", 200, quantity=5)
    c.remove_item("item", quantity=2)
    # remaining quantity 3 => subtotal 600
    assert c.subtotal() == 600.0
    with pytest.raises(ValueError):
        # removing more than present should raise ValueError (implementation may differ)
        c.remove_item("item", quantity=10)

# Coupon and shipping integration in total

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("widget", 400, quantity=3)  # subtotal 1200, free shipping
    # Apply SAVE10 coupon => 10% off: 1080
    assert c.total(coupon="SAVE10") == 1080.0
    # Now use a cheaper cart for shipping test
    d = Cart()
    d.add_item("thing", 200, quantity=3)   # subtotal 600
    # member => half shipping: coupon none
    expected_total = round(600 + shipping_fee(600, member=True), 2)
    assert d.total(member=True) == expected_total

# Edge case: empty cart total 0 (no shipping)

def test_cart_empty_total_no_shipping():
    c = Cart()
    assert c.total() == 0.0

# Coupon parsing integration: invalid coupon raises ValueError in total

def test_cart_total_invalid_coupon_raises():
    c = Cart()
    c.add_item("item", 100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
