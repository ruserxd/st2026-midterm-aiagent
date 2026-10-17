import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Helper function for floating comparison
def approx(value):
    return pytest.approx(round(value,2), rel=0.001)

# Tests for apply_discount
@ pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price,percent", [
    (-10, 20),   # negative price
    (50, -5),    # negative percent
    (30, 105),   # percent >100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# Tests for bulk_discount_percent
@ pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "", "SAV10", "SAVE51", "SAVE0", "savelater", "SAVE-5" , " SAVE 10 ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,expected", [
    (0, 60),
    (50.5, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_regular(subtotal, expected):
    assert shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Tests for Cart.total logic
def test_cart_total_no_items():
    c = Cart()
    assert c.total() == 0

def test_cart_total_simple_without_discount_and_shipping():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=3)
    # subtotal 300, no coupon, non-member: shipping 60 => total 360
    assert c.total() == 360.0

def test_cart_total_member_free_shipping_over_1000():
    c = Cart()
    c.add_item("expensive", unit_price=400, quantity=3)  # subtotal 1200
    # member pays half shipping 30 but free since >=1000? spec says if subtotal>=1000 shipping is free, so total 1200
    assert c.total(member=True) == 1200.0

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("book", unit_price=200, quantity=1)
    # subtotal 200, apply coupon SAVE10 => 180, shipping 60 -> total 240
    assert c.total(coupon="SAVE10") == 240.0

# Test bulk discount applied via add_item (implicit logic) - assuming Cart uses bulk_discount_percent internally
# We'll test that adding many units reduces unit price accordingly

def test_cart_bulk_discount():
    c = Cart()
    # Add 50 items of a product priced 10 each; bulk_discount_percent(50)=10%
    c.add_item("widget", unit_price=10, quantity=50)
    # subtotal should be 10 * 50 * (1-0.10) = 450
    assert c.subtotal() == pytest.approx(450.0, rel=0.001)

# Ensure invalid coupon in total raises ValueError

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("pen", unit_price=5, quantity=2)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
