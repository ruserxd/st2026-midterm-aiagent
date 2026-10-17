import pytest
import cart

# ---------- Helper functions for expected values ----------

def expected_bulk_discount(quantity):
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_zero_percent():
    assert cart.apply_discount(500, 0) == 500.0


def test_apply_discount_full_percent():
    assert cart.apply_discount(300, 100) == 0.0


def test_apply_discount_rounding():
    # 1% of 333 => 3.33, remaining 329.67 rounded to 2 decimals
    assert cart.apply_discount(333, 1) == round(333 * (1 - 0.01), 2)


def test_apply_discount_invalid_price_negative():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 5)


def test_apply_discount_invalid_percent_out_of_range_low():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)


def test_apply_discount_invalid_percent_out_of_range_high():
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_none():
    assert cart.bulk_discount_percent(1) == 0


def test_bulk_discount_percent_ten_units():
    assert cart.bulk_discount_percent(10) == 5


def test_bulk_discount_percent_fifty_units():
    assert cart.bulk_discount_percent(50) == 10


def test_bulk_discount_percent_hundred_units():
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_boundary_values():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_invalid_quantity_zero():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)


def test_bulk_discount_percent_invalid_quantity_negative():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_uppercase():
    assert cart.parse_coupon("SAVE10") == 10


def test_parse_coupon_valid_lowercase_and_whitespace():
    assert cart.parse_coupon("  save20 ") == 20


def test_parse_coupon_invalid_missing_prefix():
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")


def test_parse_coupon_invalid_non_integer_suffix():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEx")


def test_parse_coupon_invalid_out_of_range():
    for code in ["SAVE0", "SAVE51"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_free_for_large_subtotal():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.50) == 0


def test_shipping_fee_standard_non_member():
    assert cart.shipping_fee(200) == 60


def test_shipping_fee_half_for_members():
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_fee_invalid_negative_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-50)

# ---------- Cart class tests ----------

def test_cart_initial_state_is_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_cart_add_and_remove_item_basic():
    c = cart.Cart()
    c.add_item("apple", 2.00, 3)
    assert c.items() == {"apple": 3}
    # subtotal should apply bulk discount for quantity 3 -> no discount
    assert c.subtotal() == round(2.0 * 3, 2) == 6.0


def test_cart_add_existing_item_increases_quantity():
    c = cart.Cart()
    c.add_item("apple", 1.00, 5)
    c.add_item("apple", 1.00, 7)
    assert c.items() == {"apple": 12}


def test_cart_add_existing_item_wrong_price_raises():
    c = cart.Cart()
    c.add_item("apple", 1.00, 2)
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50, 3)


def test_cart_remove_quantity_reduces_and_removes_if_zero():
    c = cart.Cart()
    c.add_item("banana", 0.5, 4)
    c.remove_item("banana", 2)
    assert c.items() == {"banana": 2}
    # Removing all should remove the item; test bug
    c.remove_item("banana", 2)
    assert "banana" not in c.items()


def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear")


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    # subtotal 200, coupon SAVE10 => 180; shipping fee on 200 -> 60
    c.add_item("widget", 100.0, 2)
    assert c.total(coupon="SAVE10") == round(180 + 60, 2) == 240.0


def test_cart_total_member_discount_shipping_half():
    c = cart.Cart()
    c.add_item("gadget", 200.0, 1)
    # subtotal 200, coupon none, member: shipping half 30
    assert c.total(member=True) == round(200 + 30, 2) == 230.0


def test_cart_total_free_shipping_on_large_subtotal():
    c = cart.Cart()
    c.add_item("premium", 500.0, 3)  # subtotal 1500 >=1000
    assert c.total() == round(1500 + 0, 2)

# ---------- Detect implementation bugs ----------

def test_cart_remove_quantity_negative_bug():
    """
    The current implementation removes an item when the remaining quantity is < 0.
    This means that if we remove exactly the existing quantity, the item remains with a
    zero quantity, which is incorrect according to the specification.
    """
    c = cart.Cart()
    c.add_item("test", 1.0, 3)
    # Remove all units; spec expects the item to be removed entirely
    c.remove_item("test", 3)
    assert "test" not in c.items(), "Item should be removed when quantity reaches zero"


def test_cart_total_shipping_on_subtotal_after_coupon_bug():
    """
    The specification requires shipping_fee() to be computed on the subtotal after applying
    any coupon discount.  The current implementation mistakenly uses the original subtotal.
    This test demonstrates the discrepancy for a cart where a coupon would reduce the amount
    but shipping remains based on the larger pre‑coupon value.
    """
    c = cart.Cart()
    # Subtotal 200; apply 50% coupon -> 100; shipping fee should be 60, total 160
    c.add_item("bulk", 200.0, 1)
    assert c.total(coupon="SAVE50") == round(100 + 60, 2) == 160.0

# Run all tests when executed as a script.
if __name__ == "__main__":
    pytest.main([__file__])
