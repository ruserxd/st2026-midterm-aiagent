import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_normal():
    # Basic reduction
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0
    # rounding to two decimals
    assert apply_discount(99.99, 10) == round(99.99 * 0.9, 2)

def test_apply_discount_invalid():
    with pytest.raises(ValueError):
        apply_discount(-1, 20)
    with pytest.raises(ValueError):
        apply_discount(100, -5)
    with pytest.raises(ValueError):
        apply_discount(100, 105)

# ---------- bulk_discount_percent -----------------------------------------

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
        bulk_discount_percent(-5)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save50") == 50
    assert parse_coupon("   Save20   ") == 20

def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        parse_coupon("SAVEE10")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")  # below 1%
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # above 50%
    with pytest.raises(ValueError):
        parse_coupon("10SAVE")
    with pytest.raises(ValueError):
        parse_coupon(123)  # wrong type

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee_free_and_membership():
    assert shipping_fee(1000) == 0.0
    assert shipping_fee(1500) == 0.0
    # below free threshold
    assert shipping_fee(999) == 60.0
    assert shipping_fee(200, member=True) == 30.0
    assert shipping_fee(400, member=False) == 60.0

def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart class ------------------------------------------------------

def test_cart_add_and_items():
    cart = Cart()
    assert cart.items() == {}
    cart.add_item("apple", 2.5, quantity=3)
    cart.add_item("banana", 1.0)
    assert cart.items() == {
        "apple": (2.5, 3),
        "banana": (1.0, 1),
    }

def test_cart_remove_and_quantity():
    cart = Cart()
    cart.add_item("orange", 3.0, quantity=5)
    cart.remove_item("orange", quantity=2)
    assert cart.items()["orange"] == (3.0, 3)
    # Removing more than existing should remove item entirely
    cart.remove_item("orange", quantity=5)
    assert "orange" not in cart.items()

def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item("item1", 100, quantity=2)   # subtotal 200
    cart.add_item("item2", 50, quantity=3)    # subtotal +150 => 350
    assert cart.subtotal() == 350
    # No discount or shipping
    assert cart.total() == 410.0  # 350 + shipping 60 = 410
    # Apply member shipping half and a valid coupon
    total_with_member_and_coupon = cart.total(member=True, coupon="SAVE10")
    expected = 350 * 0.9 + 30  # bulk discount not applied as quantities < 10
    assert total_with_member_and_coupon == round(expected, 2)

# ---------- Edge cases for total ------------------------------------------

def test_cart_total_bulk_discount_application():
    cart = Cart()
    # Add 12 units of a single item to trigger bulk discount
    cart.add_item("bulkitem", 10.0, quantity=12)
    # No coupon, member flag irrelevant for shipping
    assert cart.total() == round(12 * 10.0 * 0.95 + 60, 2)  # 5% bulk discount

# ---------- Invalid operations in Cart -------------------------------------

def test_cart_invalid_operations():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", -10)
    with pytest.raises(ValueError):
        cart.remove_item("nonexistent")
    # Removing from an item not in the cart should raise ValueError
    cart.add_item("exists", 5.0)
    with pytest.raises(ValueError):
        cart.remove_item("exists", quantity=2)  # only one exists
