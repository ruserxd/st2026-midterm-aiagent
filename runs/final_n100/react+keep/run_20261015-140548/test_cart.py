import pytest
from cart import (
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# Bulk discount percent should be 10% for quantity >=50
@pytest.mark.parametrize("quantity,expected", [
    (50, 10),
])
def test_bulk_discount_percent_50(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# Parse coupon case-insensitive check
@pytest.mark.parametrize("code,result", [
    ("save5", 5),
])
def test_parse_coupon_case_insensitive(code, result):
    assert parse_coupon(code) == result

# Shipping fee negative subtotal should raise ValueError
@pytest.mark.parametrize("subtotal", [-0.01, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)
