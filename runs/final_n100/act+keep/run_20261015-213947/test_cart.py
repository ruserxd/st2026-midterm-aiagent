"""
Test suite for the `cart` module.
The tests are designed to validate that the behaviour matches
the specifications declared in the function docstrings.
"""
import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent, apply_discount

# ---------- Utility functions ---------

def _create_cart_with_items(items):
    """Return a Cart instance with given items.

    ``items`` is an iterable of tuples (name, unit_price, quantity).
    """
    c = Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# ---------- parse_coupon tests ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe5  ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEX10",
    "SAVE0",
    "SAVE51",
    "NOTACODE",
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ---------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [ -1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart subtotal and total tests -----

def test_empty_cart_total_is_zero():
    c = Cart()
    assert c.subtotal() == 0
    assert c.total() == 0

def test_subtotal_and_total_without_coupon_and_membership():
    items = [
        ("item1", 100, 2),   # 200
        ("item2", 50.5, 3),  # 151.5
    ]
    c = _create_cart_with_items(items)
    assert c.subtotal() == pytest.approx(351.5)
    # No coupon; shipping should be 60 (subtotal < 1000) non-member
    expected_total = 351.5 + 60
    assert c.total() == round(expected_total, 2)

def test_total_with_coupon_and_membership():
    items = [(
        "expensive", 800, 1),   # 800
        ("cheapest", 50, 3),    # 150
    )]
    c = _create_cart_with_items(items)
    assert c.subtotal() == pytest.approx(950.0)
    # Coupon SAVE10 -> 10% off subtotal => 855.0
    # Shipping for non-member on 855: still 60 because <1000
    total_no_member = 855 + 60
    assert c.total(coupon="SAVE10") == round(total_no_member, 2)
    # Member pays half shipping: 30
    total_member = 855 + 30
    assert c.total(member=True, coupon="SAVE10") == round(total_member, 2)

def test_total_rounding():
    # subtotal that results in a non-integer after discount
    items = [("item", 333.33, 3)]  # 999.99
    c = _create_cart_with_items(items)
    assert c.subtotal() == pytest.approx(999.99)
    # Coupon SAVE10 -> 899.991
    total_before_shipping = 899.991
    shipping = shipping_fee(total_before_shipping, member=False)  # <1000 => 60
    expected_total = round(total_before_shipping + shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total

# ---------- Bulk discount (optional, but spec exists) ---------

def test_bulk_discount_percent():
    # For 1-9 items => 0%? not specified; we'll test some.
    for qty, expected in [(5, 5), (20, 10), (50, 15), (100, 20)]:
        assert bulk_discount_percent(qty) == expected

# ---------- apply_discount tests ---------

def test_apply_discount():
    assert apply_discount(200, 25) == 150
    assert apply_discount(0, 10) == 0
    # percent beyond 100 should raise? not in spec; just test typical
    assert apply_discount(50, 0) == 50

# ---------- Removing items tests ---------

def test_remove_item():
    c = Cart()
    c.add_item("item", 10, 5)
    assert len(c.items()) == 1
    c.remove_item("item", 3)
    # Quantity should reduce to 2
    for name, price, qty in c.items():
        assert name == "item"
        assert qty == 2
    c.remove_item("item", 2)  # remove all
    assert len(c.items()) == 0

# ---------- Adding item multiple times ---------

def test_add_multiple_times():
    c = Cart()
    c.add_item("apple", 1.5, 2)
    c.add_item("apple", 1.5, 3)
    # Should aggregate quantity to 5
    for name, price, qty in c.items():
        assert name == "apple"
        assert qty == 5

# ---------- Edge cases for total: empty coupon string

def test_total_with_empty_coupon_string():
    c = _create_cart_with_items([("item", 10, 1)])
    with pytest.raises(ValueError):
        c.total(coupon="")

# ---------- Negative quantity in add_item should raise

def test_add_negative_quantity():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", 10, -1)

# ---------- Negative price in add_item should raise

def test_add_negative_price():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -5, 1)

"""
End of tests.
"""
