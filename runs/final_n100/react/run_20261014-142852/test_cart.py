import pytest
from cart import Cart, parse_coupon, apply_discount, bulk_discount_percent, shipping_fee

# Helper: create cart with one item
def make_cart_with_item(price, qty=1):
    c = Cart()
    c.add_item("item", price, qty)
    return c

# Test 1: Empty cart total is zero (no shipping)
@pytest.mark.parametrize("member,coupon", [(True, None), (False, None)])
def test_empty_cart_total_zero(member, coupon):
    c = Cart()
    assert c.total(member=member, coupon=coupon) == 0.0

# Test 2: subtotal calculation and total with no coupon or shipping when price is zero
def test_subtotal_and_total_no_shipping():
    c = Cart()
    c.add_item("free", 0)
    assert c.subtotal() == 0
    # Shipping should not be applied when subtotal is 0
    assert c.total(coupon=None) == 0.0

# Test 3: Coupon parsing and application
@pytest.mark.parametrize(
    "code,expected_percent",
    [
        ("10OFF", 10),
        ("20%off", 20),
        ("15percent", 15),
        ("25Off", 25),
    ],
)
def test_parse_coupon_valid(code, expected_percent):
    assert parse_coupon(code) == expected_percent

@pytest.mark.parametrize("code", ["", "abc", "5", "10% off"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Test 4: total applies coupon discount before shipping
def test_total_with_coupon_and_shipping():
    c = Cart()
    # Add an item costing $100, quantity 1
    c.add_item("widget", 100)
    # Apply a 10% off coupon
    assert c.total(coupon="10OFF") == pytest.approx(110.0)  # 90 subtotal + 20 shipping (shipping is 10% of 90? depends)

# Since shipping_fee implementation not specified, test that shipping is added correctly for known subtotal
# We'll compute expected using shipping_fee function directly

def test_total_with_shipping_computed():
    c = Cart()
    c.add_item("item", 50)  # subtotal 50
    # No coupon
    subtotal = c.subtotal()
    expected_shipping = shipping_fee(subtotal)
    expected_total = round(subtotal + expected_shipping, 2)
    assert c.total(coupon=None) == expected_total

# Test 5: Member discount via total method (member flag should reduce shipping?)
# Assuming shipping_fee accepts member argument to give lower rate; test that

def test_member_shipping_discount():
    c = Cart()
    c.add_item("item", 100)
    subtotal = c.subtotal()
    shipping_non_member = shipping_fee(subtotal, member=False)
    shipping_member = shipping_fee(subtotal, member=True)
    assert shipping_member < shipping_non_member

# Test 6: apply_discount function applies correct percentage

def test_apply_discount():
    assert apply_discount(100, 10) == 90.0
    assert apply_discount(200, 25) == 150.0

# Test 7: bulk discount percent calculation (if defined by quantity)

def test_bulk_discount_percent():
    # No specification; just ensure function exists and returns int for given qty
    assert isinstance(bulk_discount_percent(1), int)
    assert isinstance(bulk_discount_percent(10), int)

# Test 8: adding and removing items updates subtotal correctly
def test_add_remove_items_updates_subtotal():
    c = Cart()
    c.add_item("a", 30, quantity=2)   # $60
    c.add_item("b", 20, quantity=1)   # $80 total
    assert c.subtotal() == 80
    c.remove_item("a", quantity=1)    # remove one a => $50
    assert c.subtotal() == 50
    c.remove_item("b")                # remove all b => $30
    assert c.subtotal() == 30
    c.remove_item("a")                # remove remaining a => $0
    assert c.subtotal() == 0
    # Removing non-existent item should not error
    c.remove_item("c")

# Test 9: total with multiple items and coupon reduces correctly before shipping
def test_total_multiple_items_coupon():
    c = Cart()
    c.add_item("item1", 40, quantity=2)   # subtotal $80
    c.add_item("item2", 20, quantity=1)   # subtotal $100
    assert c.subtotal() == 100
    # Apply 10% coupon => 90 before shipping
    total = c.total(coupon="10OFF")
    expected_total = round(90 + shipping_fee(90), 2)
    assert total == expected_total

# Test 10: rounding to two decimals
def test_total_rounding():
    c = Cart()
    # Price that results in many decimal places when shipping added
    c.add_item("item", 33.333, quantity=3)  # subtotal 99.999
    # No coupon
    total = c.total(coupon=None)
    assert isinstance(total, float)
    assert round(total, 2) == total
