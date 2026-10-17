import pytest
import cart

# ---------- bulk_discount_percent ----------
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
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "10"])
def test_bulk_discount_percent_invalid_inputs(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (1000, 10, 900.0),
        (123.45, 20, round(98.76, 2)),
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (100, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart subtotal and total ----------
class DummyCart(cart.Cart):
    def __init__(self):
        super().__init__()

# Helper to create a cart with items

def make_cart(items):
    c = cart.Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

@pytest.mark.parametrize(
    "items,expected_subtotal",
    [
        ([], 0),
        ([("item", 100, 1)], 100.0),
        ([("bulk10", 10, 10)], round(10 * 10 * 0.95, 2)),
        ([("bulk50", 5, 50)], round(5 * 50 * 0.90, 2)),
        ([("bulk100", 20, 120)], round(20 * 120 * 0.85, 2)),
    ],
)
def test_cart_subtotal(items, expected_subtotal):
    c = make_cart(items)
    assert c.subtotal() == expected_subtotal

@pytest.mark.parametrize(
    "items,coupon,member,total",
    [
        # No items -> total 0
        ([], None, False, 0),
        # Single item, no discount
        ([("item", 100, 1)], None, False, 160.0),  # 100 + shipping 60
        # With coupon
        ([("item", 200, 1)], "SAVE10", False, 216.0),
        # Coupon and member free shipping over threshold
        ([("expensive", 1200, 1)], None, True, 1200.0),  # subtotal 1200, no shipping
    ],
)
def test_cart_total(items, coupon, member, total):
    c = make_cart(items)
    assert c.total(member=member, coupon=coupon) == total

# Ensure that an invalid coupon raises ValueError in total()

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
