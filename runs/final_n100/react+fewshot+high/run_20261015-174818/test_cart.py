import pytest
import cart

# ---------- Utility function tests ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (50.0, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@pytest.mark.parametrize("price", [-1.0, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, -1, 101, 150],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100.0, percent)

# ---------- Bulk discount tests ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (101, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Coupon parsing tests ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",
        "SAVE51",
        "SAVExx",
        "NOTACODE",
        "  ",
    ],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Shipping fee tests ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0.0, False, 60),
        (999.99, True, 30),
        (1000.0, False, 0),
        (5000.0, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

@pytest.mark.parametrize(
    "name, unit_price, qty1, qty2, expected_qty",
    [
        ("apple", 100.0, 1, 2, 3),
        ("banana", 50.5, 10, 5, 15),
    ],
)
def test_cart_add_item(name, unit_price, qty1, qty2, expected_qty):
    c = cart.Cart()
    c.add_item(name, unit_price, qty1)
    c.add_item(name, unit_price, qty2)
    assert c.items()[name] == expected_qty

@pytest.mark.parametrize(
    "name, price1, price2",
    [
        ("orange", 80.0, 90.0),
        ("pear", 25.0, -5.0),
    ],
)
def test_cart_add_item_different_price_raises(name, price1, price2):
    c = cart.Cart()
    c.add_item(name, price1, 3)
    with pytest.raises(ValueError):
        c.add_item(name, price2, 1)

@pytest.mark.parametrize(
    "name, unit_price, quantity",
    [
        ("mango", -10.0, 5),
        ("peach", 30.0, 0),
        ("plum", 20.0, -2),
    ],
)
def test_cart_add_item_invalid_args(name, unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

@pytest.mark.parametrize(
    "name, unit_price, qty_initial, qty_remove, expected_remaining",
    [
        ("grape", 5.0, 10, 3, 7),
        ("melon", 12.0, 5, 5, None),   # removed entirely
    ],
)
def test_cart_remove_item(name, unit_price, qty_initial, qty_remove, expected_remaining):
    c = cart.Cart()
    c.add_item(name, unit_price, qty_initial)
    if expected_remaining is not None:
        c.remove_item(name, qty_remove)
        assert c.items()[name] == expected_remaining
    else:
        c.remove_item(name, qty_remove)
        assert name not in c.items()

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

@pytest.mark.parametrize(
    "items, expected_subtotal",
    [
        ({"itemA": (10.0, 5)}, 50.0),
        ({"itemB": (20.0, 12)}, round(20.0 * 12 * 0.95, 2)),
        ({"itemC": (30.0, 55)}, round(30.0 * 55 * 0.90, 2)),
        ({"itemD": (40.0, 120)}, round(40.0 * 120 * 0.85, 2)),
    ],
)
def test_cart_subtotal(items, expected_subtotal):
    c = cart.Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    assert c.subtotal() == pytest.approx(expected_subtotal, rel=1e-9)

@pytest.mark.parametrize(
    "items, coupon_code, member_flag, expected_total",
    [
        ({}, None, False, 0.0),
        ({"tshirt": (200.0, 3)}, None, False,
         round((200.0 * 3) + 60, 2)),
        ({"tshirt": (200.0, 3)}, None, True,
         round((200.0 * 3) + 30, 2)),
        ({"tshirt": (100.0, 1)}, "SAVE20", False,
         round(((100.0 * 1) * 0.80) + 60, 2)),
        ({"bulk_item": (400.0, 5)}, "SAVE10", True,
         round((400.0 * 5 * 0.90), 2)),
    ],
)
def test_cart_total(items, coupon_code, member_flag, expected_total):
    c = cart.Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    assert c.total(member=member_flag, coupon=coupon_code) == pytest.approx(expected_total, rel=1e-9)

# ---------- Shipping fee after coupon mismatch test ----------

def test_cart_total_shipping_fee_after_coupon_mismatch():
    # Items sum to exactly 1000 before coupon (no bulk discount).
    c = cart.Cart()
    c.add_item("item", 200.0, 5)  # subtotal = 1000
    # Apply a 10% coupon: amount after coupon = 900
    expected_total_after_coupon_and_shipping = round(900 + 60, 2)  # shipping should be 60 because 900 < 1000
    assert c.total(coupon="SAVE10", member=False) == pytest.approx(expected_total_after_coupon_and_shipping, rel=1e-9)

# ---------- Invalid coupon during total test ----------

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 50.0, 2)
    with pytest.raises(ValueError):
        c.total(coupon="NOTACODE")
