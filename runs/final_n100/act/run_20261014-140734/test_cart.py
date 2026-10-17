import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Function tests ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 10) == 90.0
    assert apply_discount(99.999, 5) == pytest.approx(94.99995, rel=1e-6)
    assert apply_discount(50, 0) == 50.0
    assert apply_discount(75, 100) == 0.0

def test_apply_discount_invalid():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)
    with pytest.raises(ValueError):
        apply_discount(50, -5)
    with pytest.raises(ValueError):
        apply_discount(50, 105)

# bulk discount spec from source

def test_bulk_discount_percent():
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(15) == 5
    assert bulk_discount_percent(20) == 10
    assert bulk_discount_percent(35) == 10
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(60) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_parse_coupon():
    # Valid "SAVE" codes only
    assert parse_coupon("SAVE5") == 5
    assert parse_coupon("SAVE50") == 50
    with pytest.raises(ValueError):
        parse_coupon("HALF")
    with pytest.raises(ValueError):
        parse_coupon("SAVE-10")


def test_shipping_fee():
    # Base fee and member rules per spec
    assert shipping_fee(0) == 60.0
    assert shipping_fee(49.99) == 60.0
    assert shipping_fee(50) == 60.0
    assert shipping_fee(1000) == 0.0
    # Member half fee when not free
    assert shipping_fee(600, member=True) == 30.0
    assert shipping_fee(900, member=True) == 30.0
    assert shipping_fee(1000, member=True) == 0.0

# ---------- Cart class tests ----------

def test_cart_basic_operations():
    cart = Cart()
    # Initially empty
    assert cart.items() == {}
    # Add items; items() returns name->quantity mapping
    cart.add_item("Apple", 1.00)
    cart.add_item("Banana", 0.50, quantity=2)
    expected_items = {"Apple": 1, "Banana": 2}
    assert cart.items() == expected_items
    # Subtotal calculation (no discount yet)
    assert cart.subtotal() == 1.00 + 0.50 * 2
    # Total without discounts or shipping fee should equal subtotal
    assert cart.total() == pytest.approx(cart.subtotal(), rel=1e-6)


def test_cart_remove_and_discounts():
    cart = Cart()
    cart.add_item("Widget", 20, quantity=12)  # bulk discount applicable
    subtotal_before = cart.subtotal()
    total_with_bulk = cart.total()
    assert total_with_bulk < subtotal_before  # discount applied
    # Remove items; check quantity updates and errors
    cart.remove_item("Widget", quantity=5)
    assert cart.items()["Widget"] == 7
    with pytest.raises(ValueError):
        cart.remove_item("Widget", quantity=10)  # would reduce to negative, removed in implementation


def test_cart_total_with_coupon_and_member():
    cart = Cart()
    cart.add_item("Laptop", 1000)
    # Apply valid coupon SAVE5 (5% discount)
    total_no_ship = cart.total(coupon="SAVE5")
    assert total_no_ship == pytest.approx(950.0, rel=1e-6)
    # Member shipping fee logic: free when subtotal >= 1000
    total_member_free_shipping = cart.total(member=True)
    assert total_member_free_shipping == pytest.approx(1000.0, rel=1e-6)
    # Non-member gets full shipping fee of 60 (though coupon not applied)
    total_non_member_with_coupon = cart.total(member=False, coupon="SAVE5")
    assert total_non_member_with_coupon == pytest.approx(950.0 + 60.0, rel=1e-6)

# Edge cases: invalid inputs

def test_cart_invalid_inputs():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("Gadget", -5.0)
    with pytest.raises(ValueError):
        cart.add_item("Gadget", 5.0, quantity=0)
