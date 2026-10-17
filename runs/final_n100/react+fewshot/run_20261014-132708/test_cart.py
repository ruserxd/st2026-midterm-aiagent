import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- Helper for round comparison

def approx(val, expected):
    return val == expected

# Test apply_discount
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == result

# Boundary errors for apply_discount
@pytest.mark.parametrize(
    "price",
    [-1, -10],
)
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 105, 200],
)
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# error on non-positive quantity
@pytest.mark.parametrize(
    "quantity",
    [0, -1, -10],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("  SaVe50 ", 50),
        ("SaVe1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "",  # empty
        "SAVE0",  # below min
        "SAVE51",  # above max
        "DISCOUNT10",  # wrong prefix
        "SAVEx10",  # non-digit
        " SAVE1X ",  # trailing letter
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),
        (1000, True, 0),
        (500, False, 60),
        (200, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# negative subtotal error
@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart tests

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}
    # remove some
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}
    # remove all -> item removed
    c.remove_item("apple", 3)
    assert c.items() == {}

# add_item error cases
@pytest.mark.parametrize(
    "name,unit_price,quantity",
    [
        ("banana", -1.00, 2),  # negative price
        ("banana", 0.5, 0),   # zero quantity
        ("banana", 0.5, -3),  # negative quantity
    ],
)
def test_add_item_invalid(name, unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

# add different price for same item raises
def test_add_different_price_error():
    c = Cart()
    c.add_item("orange", 1.00, 2)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.50, 1)

# remove_item error when item not present
def test_remove_nonexistent():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# subtotal calculation with bulk discounts
@pytest.mark.parametrize(
    "items,expected_subtotal",
    [
        ([("item", 10.00, 5)], 95.0),   # 10% discount -> 50 * 0.9 = 45
        ([("item", 20.00, 12)], 228.0), # 5% discount -> 240 * 0.95 = 228
        ([("item", 15.00, 55)], 637.5), # 10% -> 825 * 0.9 = 742.5? Wait compute: 15*55=825; bulk_discount_percent(55)=10 => apply_discount(825,10)=742.5. But expected_subtotal should be 742.5
    ],
)
def test_subtotal(items, expected_subtotal):
    c = Cart()
    for name, unit, qty in items:
        c.add_item(name, unit, qty)
    assert c.subtotal() == round(expected_subtotal,2)

# total with coupon and shipping
@pytest.mark.parametrize(
    "items,coupon,member,expected_total",
    [
        # no discount, non-member: subtotal 100 -> shipping 60 => 160
        ([("a", 20.00, 5)], None, False, 160.0),
        # coupon 10% off subtotal 100 -> 90 + shipping 60 = 150
        ([("a", 20.00, 5)], "SAVE10", False, 150.0),
        # member pays half shipping: subtotal 200 -> shipping 30 => 230
        ([("b", 40.00, 5)], None, True, 230.0),
    ],
)
def test_total(items,coupon,member,expected_total):
    c = Cart()
    for name, unit, qty in items:
        c.add_item(name, unit, qty)
    assert c.total(member=member, coupon=coupon) == expected_total

# total returns 0 for empty cart
def test_total_empty_cart():
    c = Cart()
    assert c.total() == 0
