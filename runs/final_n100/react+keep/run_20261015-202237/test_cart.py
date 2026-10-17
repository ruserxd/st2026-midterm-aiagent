import pytest
import cart

# --------- Tests for apply_discount ---------

def test_apply_discount_standard():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent", [
        (100, -5),   # negative percent
        (-50, 10),   # negative price
        (80, 120),   # percent >100
    ]
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --------- Tests for bulk_discount_percent ---------

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # implementation uses >50, so 50 -> 5
    assert cart.bulk_discount_percent(50) == 5
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 12?"
