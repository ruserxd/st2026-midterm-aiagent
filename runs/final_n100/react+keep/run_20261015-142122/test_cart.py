import pytest
import cart

# helper to assert ValueError message matches expected

def assert_raises_with_msg(exc_type, msg, func, *args, **kwargs):
    with pytest.raises(exc_type) as excinfo:
        func(*args, **kwargs)
    assert str(excinfo.value) == msg

# ---------- Tests for apply_discount ---------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_zero_percent():
    assert cart.apply_discount(50, 0) == 50.0


def test_apply_discount_full_percent():
    assert cart.apply_discount(80, 100) == 0.0


def test_apply_discount_negative_price_raises():
    assert_raises_with_msg(
        ValueError,
        "price must be >= 0",
        cart.apply_discount,
        -10,
        20
    )


def test_apply_discount_invalid_percent_below():
    assert_raises_with_msg(
        ValueError,
        "percent must satisfy 0 <= percent <= 100",
        cart.apply_discount,
        100,
        -5
    )


def test_apply_discount_invalid_percent_above():
    assert_raises_with_msg(
        ValueError,
        "percent must satisfy 0 <= percent <= 100",
        cart.apply_discount,
        100,
        105
    )

# ---------- Tests for bulk_discount_percent ---------

def test_bulk_discount_below_ten():
    assert cart.bulk_discount_percent(9) == 0


def test_bulk_discount_exact_ten():
    assert cart.bulk_discount_percent(10) == 5


def test_bulk_discount_fifty():
    # Spec: quantity >=50 gives 10%
    assert cart.bulk_discount_percent(50) == 10


def test_bulk_discount_hundred():
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_invalid_nonpositive():
    assert_raises_with_msg(
        ValueError,
        "quantity must be a positive integer",
        cart.bulk_discount_percent,
        0
    )

# ---------- Tests for parse_coupon ---------

def test_parse_coupon_valid_simple():
    assert cart.parse_coupon("SAVE10") == 10


def test_parse_coupon_valid_lowercase_and_whitespace():
    assert cart.parse_coupon("  save5 ") == 5


def test_parse_coupon_invalid_prefix():
    assert_raises_with_msg(
        ValueError,
        "coupon code must start with 'SAVE'",
        cart.parse_coupon,
        "DISCOUNT10"
    )


def test_parse_coupon_invalid_number_range():
    assert_raises_with_msg(
        ValueError,
        "discount percent must be between 1 and 50",
        cart.parse_coupon,
        "SAVE51"
    )

# ---------- Tests for shipping_fee ---------

def test_shipping_free_over_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.99) == 0


def test_shipping_regular_non_member():
    assert cart.shipping_fee(200) == 60


def test_shipping_member_half():
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_negative_subtotal_raises():
    assert_raises_with_msg(
        ValueError,
        "subtotal must be >= 0",
        cart.shipping_fee,
        -50
    )

# ---------- Tests for Cart class behavior (spec) ---------

def test_cart_add_and_items_and_subtotal_and_total_spec():
    c = cart.Cart()
    # bulk discount for 5 units is 0% -> line total 500
    c.add_item("apple", 100, quantity=5)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == 500.0
    # no coupon, non-member: shipping 60
    assert c.total(member=False) == 560.0


def test_cart_add_multiple_items_and_discount_and_member_spec():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=10)   # bulk 5% -> line total 1900 - 95.5
    c.add_item("gadget", 300, quantity=2)    # no bulk
    subtotal_expected = round(1900 * 0.95 + 600, 2)
    assert c.subtotal() == subtotal_expected
    shipping = cart.shipping_fee(subtotal_expected, member=True)
    total_expected = round(subtotal_expected + shipping, 2)
    assert c.total(member=True) == total_expected


def test_cart_coupon_and_total_spec():
    c = cart.Cart()
    c.add_item("item", 500, quantity=1)
    # subtotal 500, coupon 10% -> amount 450 + shipping 60 = 510
    assert c.total(coupon="SAVE10") == 510.0


def test_cart_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 50)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# ---------- Tests for remove_item bug detection ---------

def test_remove_item_decreases_and_removes_spec():
    c = cart.Cart()
    c.add_item("pen", 10, quantity=3)
    c.remove_item("pen", quantity=2)
    assert c.items() == {"pen": 1}


def test_remove_item_removal_when_zero_quantity_bug():
    # Spec: removing last unit should delete key
    c = cart.Cart()
    c.add_item("book", 20)
    c.remove_item("book")
    assert "book" not in c.items()
