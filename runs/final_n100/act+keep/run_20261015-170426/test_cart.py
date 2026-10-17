import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Apply discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 105, 200],
) 
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Bulk discount percent ----------

def test_bulk_discount_percent_cases():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Parse coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("   SAVE50  ") == 50

@pytest.mark.parametrize(
    "code",
    ["INVALID", "SAVExx", "SAVE0", "SAVE51", "ABCD", ""],
) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Shipping fee ----------

def test_shipping_fee_non_member():
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0


def test_shipping_fee_member():
    assert shipping_fee(999, member=True) == 30
    assert shipping_fee(1000, member=True) == 0
    assert shipping_fee(0, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart total calculations ----------

def test_cart_total_empty():
    c = Cart()
    assert c.total() == 0


def test_cart_total_no_coupon_member_and_shipping():
    c = Cart()
    c.add_item("item", unit_price=100, quantity=5)  # subtotal 500
    total = c.total(member=True)
    # subtotal 500 -> after coupon none, shipping 30 (member half of 60)
    assert round(total, 2) == 530.0


def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("item", unit_price=200, quantity=3)  # subtotal 600
    total = c.total(coupon="SAVE10")  # 10% off -> 540
    # shipping on 540 is 60 (non-member)
    assert round(total, 2) == 600.0


def test_cart_total_coupon_invalid_raises():
    c = Cart()
    c.add_item("item", unit_price=50, quantity=2)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- Bulk discount application via Cart? Not specified
# We'll assume Cart does not apply bulk discounts automatically.

# Test that Cart subtotal uses per-item prices and quantities correctly

def test_cart_subtotal_and_items():
    c = Cart()
    c.add_item("apple", 2, quantity=3)   # 6
    c.add_item("banana", 1.5, quantity=2)  # 3
    assert c.subtotal() == 9
    items = c.items()
    assert any(it["name"] == "apple" for it in items)
    assert any(it["name"] == "banana" for it in items)
