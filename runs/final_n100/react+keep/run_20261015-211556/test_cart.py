import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# -----------------------
# Helper functions
# -----------------------

def create_cart_with_items(**items):
    """Create a cart with the given items.
    Items are passed as name: (unit_price, quantity)."""
    c = Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    return c

# -----------------------
# Tests for utility functions
# -----------------------

def test_apply_discount_valid_and_bounds():
    assert apply_discount(200, 15) == 170.0
    # zero percent -> unchanged
    assert apply_discount(123.45, 0) == 123.45
    # 100% -> free
    assert apply_discount(50, 100) == 0.0


def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-10, 20)
    with pytest.raises(ValueError):
        apply_discount(10, -5)
    with pytest.raises(ValueError):
        apply_discount(10, 120)


def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(15) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15


def test_bulk_discount_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)


def test_parse_coupon_valid_and_case_insensitivity():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon(" SAVE20 ") == 20


def test_parse_coupon_errors():
    with pytest.raises(ValueError):
        parse_coupon("INVALID")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        parse_coupon("SAVEX")
    with pytest.raises(ValueError):
        parse_coupon("save51")


def test_shipping_fee():
    # Free shipping for large orders
    assert shipping_fee(1000) == 0.0
    assert shipping_fee(1500) == 0.0
    # Normal fee, non-member
    assert shipping_fee(99.9) == 60
    assert shipping_fee(500) == 60
    # Member gets half
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# -----------------------
# Tests for Cart class
# -----------------------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_item_and_items_dict():
    c = Cart()
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}
    # Adding again increases quantity
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 5}


def test_add_item_errors():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -2, 1)   # negative price
    with pytest.raises(ValueError):
        c.add_item("banana", 2, 0)    # zero quantity
    c.add_item("orange", 3, 1)
    with pytest.raises(ValueError):
        # Changing unit price of existing item should raise
        c.add_item("orange", 4, 2)


def test_remove_item_and_quantity_update():
    c = Cart()
    c.add_item("mango", 5, 3)
    c.remove_item("mango", 1)
    assert c.items() == {"mango": 2}
    # Removing more than exists removes the item
    c.remove_item("mango", 5)
    assert c.items() == {}


def test_remove_nonexistent_raises():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)


def test_subtotal_with_bulk_discounts():
    # 12 apples at $10 each -> bulk discount 5%
    c = create_cart_with_items(apples=(10, 12))
    expected = apply_discount(10 * 12, 5)  # bulk discount applied to unit price
    assert round(c.subtotal(), 2) == round(expected, 2)
    # Add another item that doesn't get a discount
    c.add_item("bread", 3, 1)
    expected += 3  # no bulk discount for quantity 1
    assert round(c.subtotal(), 2) == round(expected, 2)


def test_total_without_coupon_and_member():
    c = create_cart_with_items(books=(20, 2))  # $40 subtotal
    total_expected = shipping_fee(40) + 40
    assert round(c.total(member=False), 2) == round(total_expected, 2)
    total_expected_mem = shipping_fee(40, member=True) + 40
    assert round(c.total(member=True), 2) == round(total_expected_mem, 2)


def test_total_with_coupon():
    c = create_cart_with_items(paint=(100, 1))
    # subtotal $100, coupon SAVE10 => 90, shipping fee 60 (non-member)
    total_expected = apply_discount(100, 10) + shipping_fee(apply_discount(100, 10))
    assert round(c.total(member=False, coupon="SAVE10"), 2) == round(total_expected, 2)


def test_total_coupon_errors_and_empty_cart():
    c = Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
    # Empty cart costs nothing
    assert c.total() == 0.0
