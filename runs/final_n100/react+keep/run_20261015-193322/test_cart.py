import pytest
import cart

# ---------- Helper assertions for spec compliance ----------

def assert_raises_value_error(func, *args, **kwargs):
    with pytest.raises(ValueError):
        func(*args, **kwargs)

# ---------- Tests for bulk_discount_percent ----------

def test_bulk_discount_percent_bounds():
    # quantity thresholds
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# ---------- Tests for parse_coupon ----------

def test_parse_coupon_valid_whitespace_and_case_insensitive():
    # Valid codes, case-insensitive and whitespace ignored
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("  SaVe5  ") == 5
    # Boundaries: 1 <= N <= 50
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon(" SAVE50 ") == 50

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("NOSAVE10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon(" SAVE-5 ")

# ---------- Tests for shipping_fee ----------

def test_shipping_fee_standard_and_member_half():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(999.99, member=False) == 60
    assert cart.shipping_fee(999.99, member=True) == 30

# ----- Test that shipping fee free above threshold ----

def test_shipping_fee_free_over_1000():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0

# ---------- Tests for Cart operations ----------

def test_cart_initially_empty_and_total_zero():
    c = cart.Cart()
    assert not c.items()
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_basic():
    c = cart.Cart()
    c.add_item("apple", unit_price=1.00, quantity=3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == pytest.approx(3.00)

# --- Adding same item increments and price check ----

def test_add_same_item_increments_and_price_check():
    c = cart.Cart()
    c.add_item("banana", unit_price=2.0, quantity=2)
    # Add more with same price
    c.add_item("banana", unit_price=2.0, quantity=3)
    assert c.items() == {"banana": 5}
    # Try adding with different price
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price=2.50, quantity=1)

# --- Removing items behavior ----

def test_remove_item_basic_and_negative_quantity_behavior():
    c = cart.Cart()
    c.add_item("cherry", unit_price=0.5, quantity=10)
    c.remove_item("cherry", quantity=4)
    assert c.items() == {"cherry": 6}
    # Removing more than remaining should delete the item
    c.remove_item("cherry", quantity=10)  # line becomes negative
    assert "cherry" not in c.items()

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# ---------- Tests for subtotal bulk discount calculations ----------

def test_subtotal_with_bulk_discount_exact_thresholds_and_beyond():
    # 5 units - no discount
    c = cart.Cart(); c.add_item("item1", unit_price=20.0, quantity=5)
    assert c.subtotal() == pytest.approx(100.00)
    # 10 units - 5% discount
    c = cart.Cart(); c.add_item("item2", unit_price=20.0, quantity=10)
    assert c.subtotal() == pytest.approx(190.00)
    # 50 units - 10% discount
    c = cart.Cart(); c.add_item("item3", unit_price=20.0, quantity=50)
    assert c.subtotal() == pytest.approx(900.00)
    # 150 units - 15% discount
    c = cart.Cart(); c.add_item("item4", unit_price=20.0, quantity=150)
    assert c.subtotal() == pytest.approx(2550.00)

# ---------- Tests for total calculation and shipping fee logic -----

def test_total_without_coupon_and_member_status():
    # subtotal 200 with no bulk discount (quantity 10 units -> 5% discount)
    c = cart.Cart(); c.add_item("prod", unit_price=10.0, quantity=20)  # 200 total, 5% discount => 190
    assert c.subtotal() == pytest.approx(190.00)
    total_expected = round(c.subtotal() + cart.shipping_fee(c.subtotal()), 2)
    assert c.total() == total_expected
    # member gets half shipping
    assert c.total(member=True) == round(c.subtotal() + cart.shipping_fee(c.subtotal(), member=True), 2)

def test_total_with_coupon_and_correct_shipping_application():
    c = cart.Cart(); c.add_item("prod", unit_price=50.0, quantity=1)   # subtotal 50
    amount_after_discount = cart.apply_discount(50.0, cart.parse_coupon("SAVE10"))
    shipping_fee = cart.shipping_fee(amount_after_discount)
    total_expected = round(amount_after_discount + shipping_fee, 2)
    assert c.total(coupon="SAVE10") == total_expected

# ---------- Additional edge cases for apply_discount -----

def test_apply_discount_bounds_and_errors():
    from cart import apply_discount
    assert apply_discount(100.0, 0) == 100.0
    assert apply_discount(100.0, 100) == 0.0
    with pytest.raises(ValueError):
        apply_discount(100.0, -1)
    with pytest.raises(ValueError):
        apply_discount(100.0, 101)
