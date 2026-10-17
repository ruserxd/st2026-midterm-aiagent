import pytest
import cart

# ---------------------------------------------------------------------------
# Helper functions for expected values derived from the specifications.
# ---------------------------------------------------------------------------

def expected_apply_discount(price, percent):
    """Return price reduced by percent and rounded to two decimals."""
    return round(price * (1 - percent / 100), 2)


def expected_bulk_discount_percent(quantity):
    if quantity >= 100:
        return 15
    if quantity >= 50:
        return 10
    if quantity >= 10:
        return 5
    return 0


def expected_parse_coupon(code):
    import re
    m = re.match(r"^\s*SAVE(\d{1,2})\s*$", code, re.I)
    if not m or int(m.group(1)) > 50:
        raise ValueError("invalid coupon")
    return int(m.group(1))


def expected_shipping_fee(subtotal, member=False):
    if subtotal >= 1000:
        return 0
    fee = 60
    return fee / 2 if member else fee

# ---------------------------------------------------------------------------
# Tests for the standalone utility functions.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, expected_apply_discount(200, 15)),      # Example from spec
        (0,   0,  0.00),                                  # No discount
        (100, 100, 0.00),                                 # Full discount
    ]
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5,   expected_bulk_discount_percent(5)),
        (10,  expected_bulk_discount_percent(10)),
        (49,  expected_bulk_discount_percent(49)),
        (50,  expected_bulk_discount_percent(50)),
        (99,  expected_bulk_discount_percent(99)),
        (100, expected_bulk_discount_percent(100)),
    ]
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE5 ", 5),
    ]
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "BAD10",     # Wrong prefix
        "SAVE0",     # Too low value
        "SAVE51",    # Above max
        "SAVEXX",    # Non‑numeric
    ]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0, False, expected_shipping_fee(0)),          # Not free, regular price
        (999.99, False, expected_shipping_fee(999.99)),# Just below free threshold
        (1000, False, 0),                              # Free shipping
        (2000, True, 0),                               # Expensive order, member still free
        (500, True, expected_shipping_fee(500, True)),
    ]
)
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# ---------------------------------------------------------------------------
# Tests for the Cart class.
# ---------------------------------------------------------------------------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

@pytest.mark.parametrize(
    "name,price,quantity",
    [
        ("apple", 1.5, 3),
        ("banana", 0.75, 2),
    ]
)
def test_add_item(name, price, quantity):
    c = cart.Cart()
    c.add_item(name, price, quantity)
    # items() should list only the added item with correct quantity
    assert c.items() == {name: quantity}
    # subtotal should reflect unit_price * quantity minus bulk discount
    disc = expected_bulk_discount_percent(quantity)
    expected_subtotal = round(price * quantity * (1 - disc / 100), 2)
    assert c.subtotal() == expected_subtotal


def test_add_item_multiple_and_pricing():
    c = cart.Cart()
    c.add_item("widget", 10.0, 5)   # no bulk discount
    assert c.subtotal() == round(10.0 * 5, 2)
    c.add_item("widget", 10.0, 7)   # total now 12 → 5% discount on the whole quantity
    disc = expected_bulk_discount_percent(12)
    expected_subtotal = round(10.0 * 12 * (1 - disc / 100), 2)
    assert c.subtotal() == expected_subtotal


def test_add_item_inconsistent_price_raises():
    c = cart.Cart()
    c.add_item("gizmo", 5.0, 1)
    with pytest.raises(ValueError):
        c.add_item("gizmo", 4.9, 1)  # price mismatch

@pytest.mark.parametrize(
    "name,quantity,expected_quantity",
    [
        ("apple", 2, 1),   # remove part of quantity
        ("banana", 3, 0),  # removal brings to zero → item removed
    ]
)
def test_remove_item(name, quantity, expected_quantity):
    c = cart.Cart()
    c.add_item(name, 2.0, 5)   # start with enough quantity
    c.remove_item(name, quantity)
    if expected_quantity > 0:
        assert c.items() == {name: expected_quantity}
    else:
        assert name not in c.items()


def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# Total calculation tests – verify step‑by‑step logic

def test_total_without_discount_or_membership():
    c = cart.Cart()
    c.add_item("itemA", 100.0, 10)   # bulk discount 5% → 950.0
    total = c.total()                 # no coupon, non‑member
    # subtotal after bulk: 950.00, shipping fee 60, total 1010.00
    assert total == round(950.0 + expected_shipping_fee(950.0), 2)


def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("itemB", 200.0, 20)   # bulk discount 5% → 3800.0
    # apply coupon SAVE10 → 3420.00
    total = c.total(member=True, coupon="SAVE10")
    expected_after_coupon = round(200.0 * 20 * (1 - 5 / 100), 2)
    expected_after_coupon = round(expected_after_coupon * (1 - 10 / 100), 2)
    # shipping fee on discounted amount: not free because < 1000
    expected_shipping = expected_shipping_fee(expected_after_coupon, member=True)
    assert total == round(expected_after_coupon + expected_shipping, 2)


def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("itemC", 50.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Edge case: empty cart should never charge shipping.

def test_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0
