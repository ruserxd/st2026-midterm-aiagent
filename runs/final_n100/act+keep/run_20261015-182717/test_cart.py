import pytest
import cart

# ---------- helper functions -------------------------------------------------

def assert_raises_with_msg(exc_type, msg_substring, func, *args, **kwargs):
    with pytest.raises(exc_type) as excinfo:
        func(*args, **kwargs)
    assert msg_substring in str(excinfo.value), f"Expected error message to contain {msg_substring!r}"

# ---------- tests for simple functions -------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_rounding_and_bounds():
    # rounding
    assert cart.apply_discount(100, 33) == round(100 * (1 - 0.33), 2)
    # bounds
    for price in [0, 10, 99.99]:
        assert cart.apply_discount(price, 0) == price
        assert cart.apply_discount(price, 100) == 0.0

    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 150)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(10.5)


def test_parse_coupon():
    for code, percent in [("SAVE10", 10), ("save20", 20), (" SAVE30 ", 30)]:
        assert cart.parse_coupon(code) == percent
    # invalid cases
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon(123)


def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # members
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- tests for Cart class ---------------------------------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert list(c.items()) == []
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    assert c.items()["apple"] == 2
    c.add_item("apple", 1.5, 3)
    assert c.items()["apple"] == 5

    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)  # price mismatch
    with pytest.raises(ValueError):
        c.add_item("banana", -1, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 1, 0)

    c.remove_item("apple", 2)
    assert c.items()["apple"] == 3
    c.remove_item("apple", 3)  # should remove completely
    assert "apple" not in c.items()

    with pytest.raises(KeyError):
        c.remove_item("banana")


def test_subtotal_bulk_discount_and_rounding():
    c = cart.Cart()
    c.add_item("item", 100, 9)   # no bulk discount
    assert c.subtotal() == 900.0
    c.add_item("bulk", 200, 10)
    # bulk discount 5% on 10 units: 200*10=2000 -> 1900 after discount
    expected = 900 + cart.apply_discount(2000, 5)
    assert c.subtotal() == round(expected, 2)


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 500, 1)   # subtotal 500
    # shipping: not member, subtotal<1000 => fee 60
    assert c.total() == round(500 + 60, 2)

    # with coupon 10% discount
    assert c.total(coupon="SAVE10") == round(cart.apply_discount(500, 10) + 60, 2)

    # member should get half shipping
    assert c.total(member=True) == round(500 + 30, 2)

    # with coupon and member
    assert c.total(coupon="SAVE20", member=True) == round(cart.apply_discount(500, 20) + 30, 2)


def test_total_ships_free_for_large_subtotal():
    c = cart.Cart()
    c.add_item("expensive", 1200, 1)   # subtotal 1200
    assert cart.shipping_fee(c.subtotal(), member=False) == 0
    assert c.total() == round(1200 + 0, 2)
    assert c.total(member=True) == round(1200 + 0, 2)


def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# ---------- check that implementation follows the specification -------------

def test_cart_total_implementation_bug_detected():
    """Verify that Cart.total uses shipping_fee on the discounted amount.
    The current implementation mistakenly passes the original subtotal to
    shipping_fee. This test intentionally exposes that bug by comparing the
    expected result with the actual.
    """
    c = cart.Cart()
    c.add_item("item", 200, 1)   # subtotal 200
    amount_without_discount = c.subtotal()  # 200
    # Use a coupon to reduce amount
    discounted_amount = cart.apply_discount(amount_without_discount, 10)
    # Expected shipping fee should be based on discounted_amount
    expected_fee = cart.shipping_fee(discounted_amount, member=False)
    expected_total = round(discounted_amount + expected_fee, 2)

    actual_total = c.total(coupon="SAVE10", member=False)
    assert actual_total == expected_total, (
        f"Expected total {expected_total}, got {actual_total}. This indicates the implementation is using the original subtotal for shipping fee."
    )
