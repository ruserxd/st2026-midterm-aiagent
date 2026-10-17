import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent

# Helper for creating a cart with items
def make_cart(items):
    c = Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

# Test subtotal calculation
@pytest.mark.parametrize("items,expected", [
    ([], 0),
    ([("apple", 1.0, 3)], 3.0),
    ([("bottle", 2.5, 2), ("pen", 1.2, 5)], 2.5*2 + 1.2*5)
])
def test_subtotal(items, expected):
    c = make_cart(items)
    assert c.subtotal() == pytest.approx(expected)

# Test shipping fee rules: free over $100, else $10, member discount 20%
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 0),
    (50, False, 10.0),
    (150, False, 0.0),
    (80, True, 8.0),   # 20% off $10
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == pytest.approx(expected)

# Test coupon parsing and application
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("5OFF", 5),
])
def test_parse_coupon(code, expected):
    assert parse_coupon(code) == expected

# Invalid coupons raise ValueError
@ pytest.mark.parametrize("invalid_code", ["BADCODE", "SAVEMAX", "10SAVE"])
def test_invalid_coupon(invalid_code):
    with pytest.raises(ValueError):
        parse_coupon(invalid_code)

# Test bulk discount percentage calculation
@pytest.mark.parametrize("qty,expected", [
    (5, 0),  # less than threshold
    (10, 5),  # >= 10 items gets 5% discount
    (20, 10),  # 10% at 20+ items
])
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

# Test total with coupon and shipping
@pytest.mark.parametrize("items,coupon,member,expected", [
    ([("item", 100.0, 1)], None, False, 110.0),   # $10 shipping
    ([("item", 120.0, 1)], None, False, 120.0),   # free shipping
    ([("item", 80.0, 1)], "SAVE10", False, 90.0),  # 10% off subtotal + $10 shipping
    ([("item", 80.0, 1)], None, True, 88.0)   # member discount on shipping
])
def test_total(items, coupon, member, expected):
    c = make_cart(items)
    assert c.total(member=member, coupon=coupon) == pytest.approx(expected)

# Empty cart total is zero
@pytest.mark.parametrize("member,coupon", [(True, None), (False, None)])
def test_empty_total(member, coupon):
    c = Cart()
    assert c.total(member=member, coupon=coupon) == 0.0
