import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_bounds(price, percent, result):
    assert apply_discount(price, percent) == result

@ pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------------------------------------

def test_bulk_discount_percent_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save25 ") == 25
    assert parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["SAVEX", "save0", "save51", "12345", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(1200) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000, member=True) == 0
    assert shipping_fee(500, member=False) == 60
    assert shipping_fee(500, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ------------------------------------------------------

def test_cart_add_and_items():
    c = Cart()
    c.add_item("apple", 2.5, quantity=3)
    c.add_item("banana", 1.0)
    assert c.items() == {"apple": 3, "banana": 1}

def test_cart_remove_items():
    c = Cart()
    c.add_item("apple", 2.5, quantity=3)
    c.remove_item("apple", quantity=2)
    assert c.items()["apple"] == 1
    # Removing more than existing removes all
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()


def test_cart_subtotal_no_bulk():
    c = Cart()
    c.add_item("item", 10, quantity=5)  # below bulk threshold
    assert c.subtotal() == 50.0

def test_cart_subtotal_with_bulk():
    c = Cart()
    c.add_item("item", 10, quantity=12)  # >=10 -> 5% discount per unit
    # Each unit price after discount: 9.5, total 114
    assert c.subtotal() == round(10 * 12 * 0.95, 2)

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("expensive", 500, quantity=3)  # subtotal 1500 -> free shipping
    total = c.total(coupon="SAVE10")
    # apply coupon: 10% off -> 1350; shipping 0
    assert total == round(1500 * 0.9, 2)

def test_cart_total_non_member_shipping():
    c = Cart()
    c.add_item("medium", 300, quantity=3)  # subtotal 900 <1000 -> shipping 60
    total = c.total()
    assert total == round(900 + 60, 2)

def test_cart_total_member_shipping():
    c = Cart()
    c.add_item("medium", 300, quantity=3)  # subtotal 900 <1000 -> shipping 30
    total = c.total(member=True)
    assert total == round(900 + 30, 2)

# ---------- Empty cart ------------------------------------------------------

def test_empty_cart_totals():
    c = Cart()
    assert c.subtotal() == 0.0
    assert c.total() == 0.0
