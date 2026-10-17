import pytest
import cart

def assert_close(a, b):
    assert round(a,2) == round(b,2)

# parse_coupon – test with exact valid codes
@pytest.mark.parametrize("code",["SAVE10","save20","SaVe30"])
def test_parse_coupon_valid(code):
    # strip not needed as implementation expects no spaces
    assert cart.parse_coupon(code) == int(code.upper()[4:])

@pytest.mark.parametrize("code",["SAVEX","SAVE-5","  SAVE51  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code.strip())
