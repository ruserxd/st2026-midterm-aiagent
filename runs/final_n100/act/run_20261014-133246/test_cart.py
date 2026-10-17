import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- Tests for apply_discount -------------------------------------------------

def test_apply_discount_basic():
    """Test that discount is applied correctly and rounded to 2 decimals."""
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 25.5) == pytest.approx(75.0, rel=1e-9)


def test_apply_discount_rounding():
    """Check that rounding is to two decimal places."""
    # 99.999 after discount should round to 99.99 if percent = 0% (i.e., no change)
    assert apply_discount(99.999, 0) == 99.99
    # 100.004 after 10% discount: 90.0036 -> rounds to 90.00
    assert apply_discount(100.004, 10) == 90.00


def test_apply_discount_errors():
    """Negative price or percent outside [0,100] should raise ValueError."""
    with pytest.raises(ValueError):
        apply_discount(-5, 10)
    with pytest.raises(ValueError):
        apply_discount(50, -1)
    with pytest.raises(ValueError):
        apply_discount(50, 101)

# --- Tests for bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    """Ensure discount percent depends on quantity as per spec."""
    # 0 < q <=5 -> 0%
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(5) == 0
    # 6-10 -> 5%
    assert bulk_discount_percent(6) == 5
    assert bulk_discount_percent(10) == 5
    # 11-20 -> 10%
    assert bulk_discount_percent(15) == 10
    # >20 -> 20%
    assert bulk_discount_percent(21) == 20
    assert bulk_discount_percent(100) == 20

# --- Tests for parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    """Valid coupon codes return (discount, description)."""
    # Basic example: code 'SAVE10' -> 10% off, free shipping if member
    assert parse_coupon('SAVE10') == (10.0, "Free shipping for members")
    # Code 'BIGSALE' might be defined differently; check spec values.
    assert parse_coupon('BIGSALE') == (25.0, "Big sale! 25% off")


def test_parse_coupon_invalid():
    """Unknown coupon code raises KeyError."""
    with pytest.raises(KeyError):
        parse_coupon('UNKNOWNCODE')

# --- Tests for shipping_fee -----------------------------------------------------

def test_shipping_fee_non_member():
    """Shipping fee is 15 if subtotal < 50, otherwise free."""
    assert shipping_fee(30) == 15.0
    assert shipping_fee(49.99) == 15.0
    assert shipping_fee(50) == 0.0
    assert shipping_fee(100) == 0.0


def test_shipping_fee_member():
    """Members have free shipping regardless of subtotal."""
    assert shipping_fee(10, member=True) == 0.0
    assert shipping_fee(70, member=True) == 0.0

# --- Tests for Cart class -------------------------------------------------------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item('Apple', unit_price=1.00, quantity=3)
    cart.add_item('Banana', unit_price=0.50)
    assert len(cart.items()) == 2
    items_dict = {item['name']: item for item in cart.items()}
    assert items_dict['Apple']['quantity'] == 3
    assert items_dict['Apple']['unit_price'] == 1.00
    assert items_dict['Banana']['quantity'] == 1
    assert items_dict['Banana']['unit_price'] == 0.50


def test_cart_remove_item():
    cart = Cart()
    cart.add_item('Orange', unit_price=0.75, quantity=5)
    cart.remove_item('Orange', quantity=2)
    # Should reduce quantity to 3
    items = {i['name']: i for i in cart.items()}
    assert items['Orange']['quantity'] == 3
    # Removing more than present removes the item completely
    cart.remove_item('Orange', quantity=5)
    assert 'Orange' not in [i['name'] for i in cart.items()]


def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item('Milk', unit_price=2.50, quantity=2)  # subtotal 5.00
    cart.add_item('Bread', unit_price=1.20, quantity=3) # subtotal 3.60 -> total before discounts: 8.60
    assert pytest.approx(cart.subtotal(), rel=1e-9) == 8.6
    # No coupon, non-member
    assert cart.total() == 8.6
    # Non-member with free shipping after $50? not relevant here
    # Member: expect same subtotal but free shipping (no fee)
    assert cart.total(member=True) == 8.6
    # Apply a valid coupon that gives discount and free shipping for members
    # e.g., 'SAVE10' gives 10% off
    total_with_coupon = cart.total(coupon='SAVE10')
    expected = apply_discount(cart.subtotal(), 10)
    assert pytest.approx(total_with_coupon, rel=1e-9) == expected

# --- Edge case: large quantities for bulk discount ---------------------------------

def test_bulk_discounts_in_cart_total():
    cart = Cart()
    # Add 12 units of an item with unit price 10 -> bulk discount should be 10%
    cart.add_item('Widget', unit_price=10.0, quantity=12)
    # Subtotal before bulk discount: 120
    # Bulk discount reduces by 10% => 108
    expected = apply_discount(120, 10)
    assert pytest.approx(cart.total(), rel=1e-9) == expected

# --- Ensure cart totals respect member shipping rules and coupons -----------------

def test_member_with_coupon_and_free_shipping():
    cart = Cart()
    cart.add_item('ItemA', unit_price=100.0)
    # subtotal 100, no shipping fee normally; member remains free
    assert cart.total(member=True) == 100.0
    # apply coupon that gives free shipping to non-members? Not needed here.
    # Ensure shipping_fee logic integrated: if subtotal >=50 free for everyone
    # Let's test with lower subtotal but member still free
    cart2 = Cart()
    cart2.add_item('Cheap', unit_price=10.0)
    assert cart2.total(member=True) == 10.0

# --- Test that add_item raises error on negative price or quantity -----------------

def test_add_item_errors():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item('Bad', unit_price=-5)
    with pytest.raises(ValueError):
        cart.add_item('Zero', unit_price=1, quantity=0)

# --- Test that remove_item raises error when trying to remove non-existent item ---------

def test_remove_nonexistent():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item('Ghost')
