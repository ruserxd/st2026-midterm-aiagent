import pytest
import cart

# Helper to assert ValueError with message containing expected substring
def assert_raises_value_error(callable_, *args, **kwargs):
    try:
        callable_(*args, **kwargs)
    except ValueError as exc:
        return str(exc)
    raise AssertionError("Expected ValueError")

# -------------------------------------------------------------------------
# Test apply_discount specification
# -------------------------------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_bounds():
    # percent outside [0,100]
    with pytest.raises(ValueError):
        cart.apply_discount(10, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 101)

    # price negative
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 20)

# -------------------------------------------------------------------------
# Test bulk_discount_percent specification
# -------------------------------------------------------------------------

def test_bulk_discount_percent_ranges():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
# -------------------------------------------------------------------------
# Test parse_coupon specification
# -------------------------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("  save20 ") == 20
    # check case-insensitivity and surrounding whitespace
    assert cart.parse_coupon("sAvE5") == 5


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")   # below min
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE60")  # above max
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        cart.parse_coupon("" )
# -------------------------------------------------------------------------
# Test shipping_fee specification
# -------------------------------------------------------------------------

def test_shipping_fee_free_and_member():
    assert cart.shipping_fee(1000, member=False) == 0
    assert cart.shipping_fee(1500, member=True) == 0
    # below threshold, non-member
    assert cart.shipping_fee(500, member=False) == 60
    # below threshold, member
    assert cart.shipping_fee(300, member=True) == 30


def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)
# -------------------------------------------------------------------------
# Cart class tests
# -------------------------------------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 100, quantity=2)
    assert c.items() == {"apple": 2}
    # add same item increases quantity
    c.add_item("apple", 100, quantity=3)
    assert c.items() == {"apple": 5}
    # adding with different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 90)


def test_cart_add_invalid_inputs():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", -10)
    with pytest.raises(ValueError):
        c.add_item("pear", 20, quantity=0)
    with pytest.raises(ValueError):
        c.add_item("pear", 20, quantity=-3)


def test_cart_remove_and_empty():
    c = cart.Cart()
    c.add_item("banana", 50, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items() == {"banana": 2}
    # removing more than remaining removes the item
    c.remove_item("banana", quantity=3)  # total now -1 => removed
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("banana")  # not present

# -------------------------------------------------------------------------
# Subtotal tests (bulk discount applied)
# -------------------------------------------------------------------------

def test_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("item", 200, quantity=5)  # bulk discount 5%
    assert c.subtotal() == round(200*5*(1-0.05),2)


def test_subtotal_multiple_items_and_discounts():
    c = cart.Cart()
    c.add_item("x", 100, quantity=9)   # 0% discount
    c.add_item("y", 50, quantity=10)   # 5%
    c.add_item("z", 200, quantity=55)  # 10%
    expected = (
        100*9 +
        apply_discount(50*10, 5) +
        apply_discount(200*55, 10)
    )
    assert c.subtotal() == round(expected,2)

# -------------------------------------------------------------------------
# Total tests (coupon and shipping)
# -------------------------------------------------------------------------

def test_total_with_coupon_and_shipping_non_member():
    c = cart.Cart()
    c.add_item("widget", 300, quantity=3)  # bulk discount 5% -> subtotal
    sub = c.subtotal()  # compute separately to compare
    # apply coupon SAVE10
    amount_after_coupon = apply_discount(sub, 10)
    shipping = cart.shipping_fee(sub, member=False)
    expected_total = round(amount_after_coupon + shipping,2)
    assert c.total(member=False, coupon="SAVE10") == expected_total


def test_total_without_coupon_member():
    c = cart.Cart()
    c.add_item("gadget", 1200, quantity=1)  # bulk discount 5%
    sub = c.subtotal()
    shipping = cart.shipping_fee(sub, member=True)
    expected_total = round(sub + shipping,2)
    assert c.total(member=True) == expected_total


def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
    # also with coupon and membership should still be 0
    assert c.total(member=True, coupon="SAVE20") == 0

# -------------------------------------------------------------------------
# Edge case: shipping fee based on subtotal after coupon as spec says.
# But implementation incorrectly uses original subtotal for shipping.
# We test to see mismatch (this will fail if bug exists).
# -------------------------------------------------------------------------

def test_shipping_fee_subtotal_after_coupon():
    # create cart with subtotal > 1000 so that normally free shipping
    c = cart.Cart()
    c.add_item("expensive", 500, quantity=3)  # 1500 -> should be free
    assert c.total(member=False) == round(c.subtotal() + cart.shipping_fee(0),2)
    # But with a coupon discount, subtotal after coupon may drop below threshold
    discounted_total = cart.total(member=False, coupon="SAVE10")
    # expected shipping fee should be based on subtotal after discount (1500*0.9=1350 >=1000 free)
    assert discounted_total == round(c.subtotal() - c.subtotal()*0.1 + 0,2)  # ensure no shipping
