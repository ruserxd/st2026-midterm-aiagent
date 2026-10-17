import pytest
from cart import (
    parse_coupon,
    apply_discount,
    bulk_discount_percent,
    shipping_fee,
    Cart,
)

# ---------- Tests for parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe30 ") == 30

@pytest.mark.parametrize(
    "code",
    ["SAVEX", "SAVE0", "SAVE51", "100SAVE", "DISCOUNT5", ""],
)
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Tests for apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(100.0, 10) == 90.0
    assert apply_discount(50, 25) == 37.5

# ---------- Tests for bulk_discount_percent ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 25
    assert bulk_discount_percent(20) == 30
    assert bulk_discount_percent(15) == 25

# ---------- Tests for shipping_fee ----------

def test_shipping_fee_non_member_low_subtotal():
    # subtotal below threshold, non-member: should incur fee
    assert shipping_fee(50.0, member=False) == pytest.approx(9.95)

def test_shipping_fee_non_member_free_threshold():
    # subtotal >= 100 free shipping
    assert shipping_fee(150.0, member=False) == 0

def test_shipping_fee_member_low_subtotal():
    # members get free shipping regardless of subtotal
    assert shipping_fee(50.0, member=True) == 0

# ---------- Tests for Cart class ----------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("Apple", 1.5)
    cart.add_item("Banana", 2.0, quantity=3)
    cart.add_item("Apple", 1.5)  # add more of existing
    items = cart.items()
    assert len(items) == 2
    # verify quantities and prices
    apple = next(it for it in items if it["name"] == "Apple")
    banana = next(it for it in items if it["name"] == "Banana")
    assert apple["quantity"] == 2
    assert apple["unit_price"] == 1.5
    assert banana["quantity"] == 3
    assert banana["unit_price"] == 2.0


def test_cart_remove_item():
    cart = Cart()
    cart.add_item("Orange", 0.8, quantity=4)
    # remove part of quantity
    cart.remove_item("Orange", quantity=2)
    assert any(it["name"] == "Orange" and it["quantity"] == 2 for it in cart.items())
    # remove remaining
    cart.remove_item("Orange", quantity=2)
    assert not any(it["name"] == "Orange" for it in cart.items())


def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item("Milk", 3.0, quantity=2)   # $6
    cart.add_item("Bread", 2.5, quantity=1)  # $2.5
    assert cart.subtotal() == pytest.approx(8.5)
    # total without shipping (subtotal >100?) no
    # subtotal 8.5 < 100 and non-member -> shipping fee applies
    expected_total = 8.5 + shipping_fee(8.5, member=False) - apply_discount(8.5, parse_coupon("SAVE10"))
    assert cart.total(member=False, coupon="SAVE10") == pytest.approx(expected_total)

# Verify that total applies member free shipping and no coupon discount when None

def test_cart_total_member_and_no_coupon():
    cart = Cart()
    cart.add_item("Item", 200.0)  # large subtotal
    assert cart.total(member=True, coupon=None) == pytest.approx(200.0)
