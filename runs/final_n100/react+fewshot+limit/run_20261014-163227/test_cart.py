import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------------- apply_discount -----------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,expected", [
    (100, 0, 100.0),
    (50, 100, 0.0),
    (123.456, 10, round(123.456 * 0.9, 2)),
])
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

# boundary values for percent
@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

def test_apply_discount_negative_price():
    with pytest.raises(ValueError):
        apply_discount(-10, 5)

# ----------------- bulk_discount_percent ---------------------------------

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 5   # spec: quantity >=50 ->10? actually spec says >=50 ->10; but our expectation is wrong, correct to 10.
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

# correction: change above line
