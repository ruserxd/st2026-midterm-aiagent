import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.9999, 10, 90.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (100, 15),
        (99, 10),
        (50, 10),
        (49, 5),
        (10, 5),
        (9, 0),
        (1, 0),
    ],
)
def test_bulk_discount_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.3],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
valid_cases = {
    "SAVE10": 10,
    "save25": 25,
    "  Save5  ": 5,
}
@pytest.mark.parametrize("code,expected", valid_cases.items())
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = ["SAV10", "SAVE0", "SAVE51", "save-1", "", "123"]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,fee",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, fee):
    assert shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal, False)

# ---------- Cart.total ----------
@pytest.fixture
def cart():
    return Cart()

# Subtotal and total calculation without coupons or shipping
@pytest.mark.parametrize(
    "items,total_expected",
    [
        ([], 0),
        ([("apple", 100, 2)], 200.0),
        ([("banana", 300, 1), ("orange", 50, 4)], 520.0),
    ],
)
def test_cart_total_no_coupon(cart, items, total_expected):
    for name, price, qty in items:
        cart.add_item(name, price, qty)
    # subtotal should match sum of unit_price*qty
    expected_subtotal = sum(price * qty for _, price, qty in items)
    assert cart.subtotal() == expected_subtotal
    # total includes shipping if subtotal>0
    if expected_subtotal > 0:
        shipping = shipping_fee(expected_subtotal, member=False)
        assert cart.total(member=False) == round(expected_subtotal + shipping, 2)
    else:
        assert cart.total(member=False) == 0

# Test coupon application and rounding
@pytest.mark.parametrize(
    "items,coupon_code,member,total_expected",
    [
        ([("item", 1000, 1)], None, False, 1000.0),  # free shipping
        ([("item", 2000, 1)], "SAVE10", False, 1800.0),
        ([("item", 200, 5)], "save5", True, 950.0),
    ],
)
def test_cart_total_with_coupon(cart, items, coupon_code, member, total_expected):
    for name, price, qty in items:
        cart.add_item(name, price, qty)
    if coupon_code is None:
        assert cart.total(member=member) == total_expected
    else:
        assert cart.total(member=member, coupon=coupon_code) == total_expected

# Invalid coupon should raise ValueError via Cart.total
@pytest.mark.parametrize("items,coupon", [([("x", 100,1)], "BADCODE")])
def test_cart_total_invalid_coupon(cart, items, coupon):
    for name, price, qty in items:
        cart.add_item(name, price, qty)
    with pytest.raises(ValueError):
        cart.total(coupon=coupon)

# Removing items and total recalculation
def test_cart_remove_and_total(cart):
    cart.add_item("red", 100, 3)
    assert cart.subtotal() == 300
    cart.remove_item("red", 1)
    assert cart.subtotal() == 200
    cart.remove_item("red", 2)  # remove all
    assert cart.subtotal() == 0
    assert cart.total(member=False) == 0
