import pytest
import cart

# ... (previous tests) ...

def test_parse_coupon_valid():
    valid_cases = ["SAVE10", " save25 ", "SaVe50"]
    for code in valid_cases:
        n = int(''.join(filter(str.isdigit, code)))
        assert cart.parse_coupon(code) == n

def test_parse_coupon_invalid():
    invalid_codes = ["SAVEXX", "SAVE0", "SAVE51", "10SAVE", "", None]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)
