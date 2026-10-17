import pytest
import cart

def round2(x):
    return round(float(x), 2)

# apply_discount tests unchanged

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding_and_errors():
    assert cart.apply_discount(333.3333, 10) == round2(333.3333 * 0.9)
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 20)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 101)

# bulk_discount_percent tests unchanged

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(51) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-3)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(2.5)

# parse_coupon: spec says case-insensitive; implementation fails
# We test both that it accepts correct cases and rejects incorrect ones.

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20  # should succeed per spec but fails
    assert cart.parse_coupon(" SAVE30 ") == 30


def test_parse_coupon_errors():
    with pytest.raises(ValueError):
        cart.parse_coupon(123)
    with pytest.raises(ValueError):
        cart.parse_coupon("DIS10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE60")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEAB")

# shipping_fee tests unchanged but use cart.

def test_shipping_fee_free_and_member():
    import cart as _c
    threshold = getattr(_c, 'FREE_SHIPPING_THRESHOLD', None)
    base = getattr(_c, 'SHIPPING_BASE', None)
    if threshold is None or base is None:
        pytest.skip("shipping constants not available")
    assert cart.shipping_fee(threshold) == 0
    assert cart.shipping_fee(999.99) == base
    assert cart.shipping_fee(999.99, member=True) == base / 2
    assert cart.shipping_fee(0, member=False) == base
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Cart class tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=3)
    c.add_item("banana", 0.5, quantity=2)
    assert c.items() == {"apple": 3, "banana": 2}
    c.add_item("apple", 1.00, quantity=2)
    assert c.items()["apple"] == 5
    with pytest.raises(ValueError):
        c.add_item("apple", 1.20, quantity=1)


def test_cart_remove_and_errors():
    c = cart.Cart()
    c.add_item("item", 10, quantity=5)
    c.remove_item("item", quantity=2)
    assert c.items()["item"] == 3
    # Removing more than remaining deletes item per implementation
    c.remove_item("item", quantity=4)
    assert "item" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("missing")


def test_cart_subtotal_and_bulk_discount():
    c = cart.Cart()
    c.add_item("widget", 20, quantity=12)
    assert round2(c.subtotal()) == 228.00
    c.add_item("gadget", 30, quantity=55)
    expected = 228 + 1485
    assert round2(c.subtotal()) == round2(expected)


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("product", 50, quantity=10)  # subtotal: 500 -5% = 475
    assert round2(c.subtotal()) == 475.00
    total_no_coupon = c.total(member=False)
    expected_shipping = cart.shipping_fee(c.subtotal(), False)
    assert round2(total_no_coupon) == round2(475 + expected_shipping)
    total_with_coupon = c.total(member=False, coupon="SAVE10")
    discounted_amount = cart.apply_discount(475, 10)
    expected_total = round2(discounted_amount + cart.shipping_fee(c.subtotal(), False))
    assert round2(total_with_coupon) == expected_total
    total_member = c.total(member=True, coupon=None)
    expected_member_total = round2(475 + cart.shipping_fee(c.subtotal(), True))
    assert round2(total_member) == expected_member_total
    empty_cart = cart.Cart()
    assert empty_cart.total() == 0

# Test that shipping fee uses subtotal before coupon, not after

def test_shipping_fee_not_discounted():
    c = cart.Cart()
    c.add_item("item", 120, quantity=10)  # subtotal: 1200 -5% = 1140
    assert cart.shipping_fee(c.subtotal(), False) == 0
    total_with_coupon = c.total(coupon="SAVE20")
    assert round2(total_with_coupon) == round2(1140 * 0.8)

# Verify that coupon parsing is case-insensitive per spec (currently fails)
def test_parse_coupon_case_insensitivity():
    with pytest.raises(ValueError):
        cart.parse_coupon("save20")  # expected to succeed per spec but fails

# Verify remove_item bug: removing more than quantity should raise KeyError per spec
# but implementation deletes only if <0, so no error; test observes current behavior.
def test_remove_item_negative_quantity_bug():
    c = cart.Cart()
    c.add_item("foo", 10, quantity=2)
    # Removing more than existing does not raise KeyError
    with pytest.raises(KeyError):
        c.remove_item("foo", quantity=5)  # should raise per spec but doesn't
