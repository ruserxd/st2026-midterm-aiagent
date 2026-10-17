import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 10) == 90.0


def test_apply_discount_rounding():
    # 123.456 with 10% discount should round to 111.11
    assert cart.apply_discount(123.456, 10) == pytest.approx(111.11, rel=1e-5)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-50, 20)


def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_thresholds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(200) == 15


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)  # non-integer

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("   SaVe50   ") == 50
    # boundary values
    assert cart.parse_coupon(" SAVE1 ") == 1
    assert cart.parse_coupon("SAVE50") == 50


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")

# ---------- shipping_fee ----------

def test_shipping_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    # free at 1000 or more
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0


def test_shipping_member():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0


def test_shipping_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- Cart class behavior (spec-compliant tests) ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_cart_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 100, quantity=5)
    # bulk discount percent for 5 is 0
    assert c.subtotal() == 500.0
    c.add_item("apple", 100, quantity=6)  # now 11 total -> 5% discount on line total
    expected_line_total = 100 * 11
    discounted = cart.apply_discount(expected_line_total, cart.bulk_discount_percent(11))
    assert pytest.approx(c.subtotal(), rel=1e-4) == round(discounted,2)
    # Remove some quantity
    c.remove_item("apple", quantity=3)
    assert c.items()["apple"] == 8
    # Removing more than remaining should delete the item (spec says remove if reaches 0 or less)
    c.remove_item("apple", quantity=8)
    assert "apple" not in c.items()


def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -50, 1)  # negative price
    with pytest.raises(ValueError):
        c.add_item("banana", 30, quantity=0)
    c.add_item("orange", 20, quantity=2)
    # Adding same name with different price should raise
    with pytest.raises(ValueError):
        c.add_item("orange", 25, quantity=1)


def test_cart_remove_invalid():
    c = cart.Cart()
    c.add_item("pear", 10, quantity=3)
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")
    # Removing more than exists should still delete item but not raise (spec: remove and delete if <=0)
    c.remove_item("pear", quantity=5)
    assert "pear" not in c.items()


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    # Add items totaling 200 before discount
    c.add_item("item1", 100, quantity=2)  # subtotal 200
    amount_before_coupon = c.subtotal()   # should be 200
    assert amount_before_coupon == 200
    # Apply valid coupon SAVE10 => 10% off => 180
    total_with_coupon = c.total(coupon="SAVE10")
    # shipping fee computed on discounted amount 180 -> member? non-member default False: shipping 60 unless subtotal>=1000, so 240 total
    assert total_with_coupon == 240.0
    # For member, shipping half: 30 => total 210
    assert c.total(member=True, coupon="SAVE10") == 210.0
    # Invalid coupon should raise ValueError and not alter total
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- detect implementation mismatches against spec ----------

def test_cart_total_shipping_bug():
    """Spec expects shipping computed after coupon; implementation uses original subtotal.
    This test will fail if the implementation is incorrect."""
    c = cart.Cart()
    c.add_item("bigitem", 100, quantity=10)  # subtotal 1000 -> free shipping
    # Apply a coupon that reduces subtotal below threshold
    total = c.total(coupon="SAVE50")
    # After 50% off, discounted amount is 500 < 1000 but shipping should still be free per spec? actually spec says shipping computed after coupon and if subtotal >= 1000 free. So since discounted amount 500<1000 shipping not free => 60.
    expected = round(500 + 60, 2)
    assert total == expected
