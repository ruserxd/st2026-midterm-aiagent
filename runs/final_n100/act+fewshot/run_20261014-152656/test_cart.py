import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1,10),(100,-5),(100,105)])
def def test_apply_discount_errors(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)
PY
