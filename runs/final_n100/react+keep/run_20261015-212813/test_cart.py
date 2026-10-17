import pytest
import cart

# Helper to compare floats
from math import isclose

def test_parse_coupon_valid_and_invalid():
    # valid cases (case-insensitive, whitespace ignored)
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("  save20   ") == 20
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT5")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEBAD")
    # out of bounds percent
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE60")

# Test bulk_discount_percent behavior
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (20, 5),
        (51, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Test apply_discount with various inputs
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 0, 200.00),
        (200, 15, 170.00),
        (123.45, 10, 111.11),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Test Cart subtotal calculations with bulk discounts
@pytest.mark.parametrize(
    "items, expected",
    [
        ([("apple", 10.0, 5)], 50.00), # no discount
        ([("banana", 20.0, 10)], round(20*10* (100-5)/100,2)),
        ([("cherry", 5.0, 60)], round(5*60*(100-10)/100,2)),
    ],
)
def test_cart_subtotal(items, expected):
    c = cart.Cart()
    for name, unit, qty in items:
        c.add_item(name, unit, qty)
    assert isclose(c.subtotal(), expected, abs_tol=0.01)

# Test total without coupon or shipping when cart empty
def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# Test total with member and no coupon (shipping fee should be half)
def test_total_member_shipping_half():
    c = cart.Cart()
    c.add_item("item", 200, 1)  # subtotal 200 < FREE_SHIPPING_THRESHOLD
    amount = c.total(member=True)
    expected = round(200 + cart.shipping_fee(200, member=True),2)
    assert isclose(amount, expected, abs_tol=0.01)

# Test total with coupon applied correctly
def test_total_with_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    subtotal = c.subtotal()
    discounted = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
    expected = round(discounted + cart.shipping_fee(discounted),2)
    assert isclose(c.total(coupon="SAVE10"), expected, abs_tol=0.01)

# Test remove_item logic (bug exposed: item not removed when quantity reaches 0)
def test_remove_item_not_removed_when_zero():
    c = cart.Cart()
    c.add_item("item", 50, 2)
    # removing one should leave one
    c.remove_item("item", 1)
    assert "item" in c.items() and c.items()["item"] == 1
    # removing the last unit should delete the item (bug: currently not because <0)
    c.remove_item("item", 1)
    assert "item" not in c.items()

# Test remove_item raises KeyError for non-existing item
def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("ghost")
