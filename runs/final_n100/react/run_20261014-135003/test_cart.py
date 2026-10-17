import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# -----------------------
# apply_discount tests
# -----------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # rounding to two decimals
    assert apply_discount(100.123, 20) == round(100.123 * 0.8, 2)

@pytest.mark.parametrize("price,percent", [(-10, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# -----------------------
# bulk_discount_percent tests
# -----------------------

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# -----------------------
# parse_coupon tests
# -----------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("   Save50  ") == 50

@pytest.mark.parametrize("code", ["SAVEXX", "SAVE0", "SAVE51", "INVALID", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# -----------------------
# shipping_fee tests
# -----------------------

def test_shipping_fee_free_and_paid():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    # members pay half
    assert shipping_fee(50, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30
    # free for subtotal >= 1000
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# -----------------------
# Cart tests
# -----------------------

def test_cart_add_and_remove():
    c = Cart()
    # Add new item
    c.add_item("Apple", 1.5, 3)
    assert c.items() == {"Apple": (1.5, 3)}
    # Add same item with same price increases quantity
    c.add_item("Apple", 1.5, 2)
    assert c.items()["Apple"] == (1.5, 5)
    # Adding same item with different price raises error
    with pytest.raises(ValueError):
        c.add_item("Apple", 2.0)

    # Remove quantity less than current
    c.remove_item("Apple", 2)
    assert c.items()["Apple"] == (1.5, 3)
    # Removing more than exists raises ValueError
    with pytest.raises(ValueError):
        c.remove_item("Apple", 10)
    # Remove item completely
    c.remove_item("Apple", 3)
    assert "Apple" not in c.items()

def test_cart_subtotal_and_total():
    c = Cart()
    c.add_item("Book", 12.0, 2)      # $24
    c.add_item("Pen", 1.5, 10)       # bulk discount for pens (10 units -)
    subtotal = c.subtotal()
    assert subtotal == pytest.approx(24 + 1.5 * 10)

    # Total without member or coupon: add shipping fee 60
    total_no_discount = c.total(member=False, coupon=None)
    expected_total = round(subtotal + 60, 2)
    assert total_no_discount == expected_total

    # Member gets half shipping
    total_member = c.total(member=True)
    assert total_member == round(subtotal + 30, 2)

    # Apply coupon SAVE10 - 10% discount on subtotal
    total_coupon = c.total(coupon="SAVE10")
    discounted_subtotal = round(subtotal * 0.9, 2)
    expected = round(discounted_subtotal + 60, 2)
    assert total_coupon == expected
