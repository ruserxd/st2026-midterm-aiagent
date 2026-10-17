import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

def test_apply_discount_zero_and_full():
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

@pytest.mark.parametrize("price,percent", [(-1,10), (50,-5), (50,105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize("code", ["", "A1", "SAVEX", "SAVE0", "SAVE51", "save-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(200, member=False) == 60

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart total logic ----------

def test_cart_total_empty():
    c = Cart()
    assert c.total() == 0.0

def test_cart_total_no_coupon_non_member():
    c = Cart()
    c.add_item("widget", 100, 2)   # subtotal=200
    assert c.subtotal() == 200
    assert c.total() == 260  # +60 shipping

def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("gadget", 500, 1)
    # subtotal 500, apply coupon SAVE10 -> 450, shipping for member half of 60=30
    assert c.total(member=True, coupon="SAVE10") == 480.0

# Test that invalid coupon raises ValueError in total()
def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("thing", 100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Ensure rounding to two decimals

def test_cart_rounding():
    c = Cart()
    c.add_item("odd", 33.333, 3)   # subtotal=99.999
    # No coupon, shipping 60 -> total should be rounded to 159.999 ≈ 160.00
    assert c.total() == 160.0
