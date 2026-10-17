import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Tests for apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [0, 10.5, 100])
@ pytest.mark.parametrize("percent", [0, 50, 100])
def test_apply_discount_valid_range(price, percent):
    # When percent is exactly bounds or in between, result should be price*(1 - percent/100)
    expected = round(price * (1 - percent / 100), 2)
    assert apply_discount(price, percent) == expected

# Edge cases: rounding behavior

def test_apply_discount_rounding():
    # e.g., 0.005 -> 0.00 after applying 50%
    assert apply_discount(0.01, 50) == 0.005
    # but function rounds to two decimals
    assert round(apply_discount(0.01, 50), 2) == 0.01

# Negative price or percent out of bounds should raise ValueError

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent ----------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-10)

# ---------- Tests for parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5 ") == 5
    assert parse_coupon("   SaVe30   ") == 30

@ pytest.mark.parametrize("code", ["SAVEx", "SAVE0", "SAVE51", "XYZ10", ""])
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Tests for shipping_fee ----------

def test_shipping_fee_non_members():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

def test_shipping_fee_members():
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(300, member=True) == 30
    # free for subtotal >= 1000 even for members
    assert shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart class behavior ----------

def test_cart_basic_flow():
    c = Cart()
    # Initially empty subtotal and total should be 0
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

    # Add single item
    c.add_item("apple", 100, quantity=2)
    assert c.items()["apple"] == (100, 2)
    assert c.subtotal() == 200

    # Adding same item increases quantity
    c.add_item("apple", 100, quantity=3)
    assert c.items()["apple"] == (100, 5)
    assert c.subtotal() == 500

    # Remove part of the quantity
    c.remove_item("apple", quantity=2)
    assert c.items()["apple"] == (100, 3)
    assert c.subtotal() == 300

    # Removing more than present should reduce to zero and remove key
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()
    assert c.subtotal() == 0

    # Add multiple items
    c.add_item("banana", 50, quantity=10)  # triggers bulk discount
    assert c.items()["banana"] == (50, 10)
    # Bulk discount percent for banana quantity 10 is 5%
    expected_bulk = 0.05
    # Total without coupon: subtotal - discount + shipping
    subtotal = 500
    discounted_subtotal = round(subtotal * (1 - expected_bulk), 2)
    total_expected = round(discounted_subtotal + shipping_fee(discounted_subtotal), 2)
    assert c.total() == total_expected

    # Apply coupon and verify discount applied before shipping
    total_with_coupon = c.total(coupon="SAVE10")
    # coupon percent is 10%
    discounted_after_coupon = round(subtotal * (1 - 0.10), 2)
    expected_total_coupon = round(discounted_after_coupon + shipping_fee(discounted_after_coupon), 2)
    assert total_with_coupon == expected_total_coupon

# Test Cart.total with member flag influences shipping via shipping_fee

def test_cart_member_shipping():
    c = Cart()
    c.add_item("item", 200, quantity=5)  # subtotal 1000 => free shipping regardless of membership
    assert c.total(member=True) == 1000.00
    # reduce to less than free threshold
    c.remove_item("item", quantity=1)
    # now subtotal 800; member gets half fee 30
    assert c.total(member=True) == round(800 + 30, 2)

# Test error handling in Cart methods

def test_cart_invalid_operations():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -10)
    with pytest.raises(ValueError):
        c.add_item("bad", 5, quantity=0)
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")
    # removing more than existing raises ValueError
    c.add_item("present", 20, quantity=2)
    with pytest.raises(ValueError):
        c.remove_item("present", quantity=5)
    
# Test parsing of coupon in Cart.total

def test_cart_invalid_coupon():
    c = Cart()
    c.add_item("test", 100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
