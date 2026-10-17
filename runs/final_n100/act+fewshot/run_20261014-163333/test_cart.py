import pytest
import cart

# Helper for floating comparison
from decimal import Decimal, ROUND_HALF_UP

def round2(x):
    return float(Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.00),
        (100, 0, 100.00),
        (50, 100, 0.00),
        (99.999, 20, 79.9992),  # should round to 80.00
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == round2(result)

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent", [-5, 101, 200]
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@ pytest.mark.parametrize(
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
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.2])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SaVe5 ", 5),
        ("  save50   ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVExx", "10SAVE", "SAVER", "SAVE-5", " SAVE51 "])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0.00),
        (2000, True, 0.00),
        (999.99, False, 60.00),
        (500, True, 30.00),
        (0, False, 60.00),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == round2(expected)

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal, False)

# ---------- Cart.total ----------
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.00

@ pytest.mark.parametrize(
    "items,coupon,member,total_expected",
    [
        # single item, no discount, non-member shipping
        ([{"name": "a", "unit_price": 200, "quantity": 1}], None, False, round2(260.00)),  # 200 + 60
        # single item, coupon 10%
        ([{"name": "b", "unit_price": 300, "quantity": 1}], "SAVE10", False, round2(330.00)),  # 300*0.9=270 +60
        # multiple items with bulk discount
        ([{"name": "c", "unit_price": 50, "quantity": 150}], None, False,
         round2(50 * 150 * (1 - 0.15) + 60)),
        # member pays half shipping
        ([{"name": "d", "unit_price": 1000, "quantity": 1}], None, True, round2(1000 + 30)),
    ],
)
def test_cart_total_cases(items, coupon, member, total_expected):
    c = cart.Cart()
    for itm in items:
        c.add_item(itm["name"], itm["unit_price"], itm.get("quantity", 1))
    assert c.total(member=member, coupon=coupon) == total_expected

# Validate that invalid coupon raises ValueError through total
def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("x", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
