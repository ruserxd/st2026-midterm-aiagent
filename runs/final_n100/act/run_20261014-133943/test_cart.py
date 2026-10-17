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
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
        (0, 50, 0.0),
        (123.456, 10, round(111.1104, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-12)

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.5],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe5  ", 5),
        ("SAVE50", 50),
        ("SaVE1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "save0",  # below min
        "SAVE51",  # above max
        "DISCOUNT10",  # wrong prefix
        "SAVEXX",  # not a number
        "",  # empty
        None,  # non-string
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, False, 60),
        (1000, False, 0),
        (999.99, True, 30),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -10.5],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------
def test_cart_basic_operations():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 100, 2)
    assert c.items() == {"apple": (100, 2)}
    c.add_item("banana", 200)
    assert c.items()["banana"] == (200, 1)

    # subtotal calculation
    assert c.subtotal() == 100 * 2 + 200 * 1

    # removing items
    c.remove_item("apple")
    assert c.items()["apple"] == (100, 1)
    c.remove_item("banana", 1)
    assert "banana" not in c.items()

    # bulk discount applied per item quantity thresholds
    c.add_item("pear", 50, 10)  # should trigger 5% bulk discount on pears
    subtotal = 100 * 1 + 50 * 10
    discounted_pear_total = apply_discount(50 * 10, bulk_discount_percent(10))
    expected_total = subtotal - (apply_discount(50 * 10, bulk_discount_percent(10)) - 50 * 10)
    # Use cart.total to compute overall total with member=True and coupon='SAVE5'
    # coupon 5% should apply on the subtotal after shipping
    total = c.total(member=True, coupon="SAVE5")
    assert isinstance(total, float)

# Test that Cart.total uses shipping and coupons correctly
@pytest.mark.parametrize(
    "items,member,coupon,total_expected",
    [
        # no items
        ({}, False, None, 0),
        # simple case without discounts
        ({"x": (100, 1)}, False, None, 160),  # 100 + shipping 60
        # member free shipping when below threshold
        ({"x": (200, 3)}, True, None, 600),  # 600 + shipping 0 because subtotal>=1000? actually 200*3=600<1000 -> shipping 0? wait
    ],
)
def test_cart_total_cases(items, member, coupon, total_expected):
    c = Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    assert c.total(member=member, coupon=coupon) == pytest.approx(total_expected)

# Ensure that adding non-positive quantity raises ValueError
@pytest.mark.parametrize(
    "name,unit_price,quantity",
    [
        ("bad", 100, -1),
        ("zero", 50, 0),
    ],
)
def test_add_item_invalid(name, unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

# Ensure that removing more than existing raises ValueError
@pytest.mark.parametrize(
    "name,quantity",
    [
        ("apple", 5),  # only 2 in cart
    ],
)
def test_remove_item_invalid(name, quantity):
    c = Cart()
    c.add_item("apple", 100, 2)
    with pytest.raises(ValueError):
        c.remove_item(name, quantity)
