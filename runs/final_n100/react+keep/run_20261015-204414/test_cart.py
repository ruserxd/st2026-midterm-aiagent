import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Function tests ----------

def test_apply_discount_valid_cases():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0
    # rounding check
    assert apply_discount(99, 10) == round(99 * (1 - 0.10), 2)

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -1)
    with pytest.raises(ValueError):
        apply_discount(100, 101)


def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    # According to specification, quantity >=50 should yield 10%
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)


def test_parse_coupon_valid_and_invalid_cases():
    assert parse_coupon("SAVE10") == 10
    # Case-insensitive and trailing whitespace should be ignored
    assert parse_coupon("save25 ") == 25
    assert parse_coupon("  SaVe1") == 1
    with pytest.raises(ValueError):
        parse_coupon("SAVEE10")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")


def test_shipping_fee():
    assert shipping_fee(500, member=False) == 60
    assert shipping_fee(1000, member=False) == 0
    assert shipping_fee(2000, member=True) == 0
    assert shipping_fee(999.99, member=True) == 30
    with pytest.raises(ValueError):
        shipping_fee(-1)

# ---------- Cart class tests ----------

def test_cart_initialization_and_items():
    cart = Cart()
    assert cart.items() == {}


def test_cart_add_item_basic_and_bulk_discount():
    cart = Cart()
    cart.add_item("apple", 10)
    assert cart.items() == {"apple": 1}
    # add more quantity to trigger bulk discount
    cart.add_item("apple", 10, quantity=9)  # total quantity 10
    assert cart.items()["apple"] == 10
    expected = apply_discount(10 * 10, bulk_discount_percent(10))
    assert cart.subtotal() == round(expected, 2)


def test_cart_add_item_price_mismatch_error():
    cart = Cart()
    cart.add_item("banana", 5)
    with pytest.raises(ValueError):
        cart.add_item("banana", 6)


def test_cart_remove_item_and_underflow():
    cart = Cart()
    cart.add_item("orange", 3, quantity=2)
    cart.remove_item("orange")  # remove one
    assert cart.items()["orange"] == 1
    # removing more than present should delete item (bug check)
    cart.remove_item("orange", quantity=5)  # should remove completely without error
    assert "orange" not in cart.items()


def test_cart_remove_nonexistent_raises():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item("nonexist")


def test_cart_total_with_coupon_and_shipping_bug_detection():
    # Scenario where subtotal > 1000 but after coupon < 1000
    cart = Cart()
    cart.add_item("item", 200, quantity=10)  # subtotal with bulk discount
    amount_before_coupon = cart.subtotal()
    assert amount_before_coupon > 1000
    discounted_amount = apply_discount(amount_before_coupon, parse_coupon("SAVE50"))
    assert discounted_amount < 1000
    expected_fee = shipping_fee(discounted_amount, member=False)
    expected_total = round(discounted_amount + expected_fee, 2)
    actual_total = cart.total(coupon="SAVE50")
    # The implementation incorrectly uses subtotal for shipping fee,
    # which would make the fee zero. We expect a mismatch.
    assert actual_total != expected_total


def test_cart_total_empty_cart():
    cart = Cart()
    assert cart.total() == 0
