import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# Tests for apply_discount

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# Tests for bulk_discount_percent

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# Tests for parse_coupon

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe30  ") == 30

@pytest.mark.parametrize("code", ["", "ABC", "SAVEXY", "SAVE0", "SAVE51", "1234"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee

def test_shipping_fee_basic():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(1500, member=False) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)
