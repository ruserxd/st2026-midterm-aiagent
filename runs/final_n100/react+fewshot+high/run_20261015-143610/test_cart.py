import pytest
import cart

# apply_discount tests
def test_apply_discount_basic():
    # Basic examples from spec
    assert cart.apply_discount(200, 15) == 170.0
    # Rounding to two decimals
    expected = round(19.9999 * (1 - 10/100), 2)
    assert cart.apply_discount(19.9999, 10) == expected
    # Simple half discount
    assert cart.apply_discount(20, 50) == 10.0

# Edge cases for apply_discount
def test_apply_discount_edge_cases():
    # Percent boundaries
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

# Invalid inputs for apply_discount
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 101)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid inputs for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SAVE30   ", 30),
    ("SaVe50", 50)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupon codes
@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAV10",
    "XYZ10",
    "save-5",
    "SAVE10.5",
    "SAVE ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, False, 0),
    (2000, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Invalid subtotal for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)
