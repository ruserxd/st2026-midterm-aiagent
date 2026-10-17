import pytest
from cart import Cart, parse_coupon

# ---------- coupon parsing tests ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SAVE30   ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", [
    "SAV10",
    "SAVE51",
    "SAVE0",
    "12345",
    "",
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        parse_coupon(invalid_code)

# ---------- subtotal calculation tests ----------

@pytest.mark.parametrize("items,expected", [
    # No items
    ([], 0.00),
    # Single item no bulk discount
    ([{"name": "A", "unit_price": 10.0, "quantity": 1}], 10.0),
])
def test_subtotal_simple(items, expected):
    cart = Cart()
    for it in items:
        cart.add_item(it["name"], it["unit_price"], it["quantity"])
    assert pytest.approx(cart.subtotal(), rel=1e-9) == expected

# ---------- total calculation tests ----------

@pytest.mark.parametrize(
    "items,member,coupon,total_expected",
    [
        # Empty cart: total 0
        ([], False, None, 0.00),
        # No coupon, no member
        ([{"name": "B", "unit_price": 15.5, "quantity": 2}], False, None, pytest.approx(31.0)),
        # With coupon reducing subtotal by percent
        ([{"name": "C", "unit_price": 20.0, "quantity": 3}], False, "SAVE10", pytest.approx(54.0)),
    ],
)
def test_total(items, member, coupon, total_expected):
    cart = Cart()
    for it in items:
        cart.add_item(it["name"], it["unit_price"], it["quantity"])
    result = cart.total(member=member, coupon=coupon)
    assert pytest.approx(result, rel=1e-9) == total_expected

# ---------- invalid coupon in total raises ValueError ----------

def test_total_invalid_coupon():
    cart = Cart()
    cart.add_item("D", 5.0, 2)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")
