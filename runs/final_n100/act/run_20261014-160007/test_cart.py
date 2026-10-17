import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

# round to two decimals

def test_apply_discount_rounding():
    # 1.99 discounted by 33% -> 1.316... should round to 1.32
    assert apply_discount(1.99, 33) == pytest.approx(1.32, abs=0.01)

# error conditions

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -1)
    with pytest.raises(ValueError):
        apply_discount(100, 101)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_percent_errors():
    for bad in [0, -1, 3.5]:
        with pytest.raises(ValueError):
            bulk_discount_percent(bad)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE15 ") == 15

def test_parse_coupon_invalid_cases():
    for code in ["SAV10", "SAVE0", "SAVE51", "", "   ", "ABCD"]:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_membership():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart class ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0


def test_add_and_remove_items():
    c = Cart()
    c.add_item("Apple", 1.5, 3)
    assert c.items() == {"Apple": 3}
    # Adding same item increases quantity
    c.add_item("Apple", 1.5, 2)
    assert c.items() == {"Apple": 5}
    with pytest.raises(ValueError):
        c.add_item("Apple", 2.0, 1)  # different unit price
    c.remove_item("Apple", 2)
    assert c.items() == {"Apple": 3}
    c.remove_item("Apple", 3)  # remove all
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("Banana", 1)


def test_subtotal_with_bulk_discount():
    c = Cart()
    c.add_item("ItemA", 10, 9)   # <10 -> no discount
    assert c.subtotal() == 90.0
    c.add_item("ItemB", 20, 10)  # exactly 10 -> 5% bulk discount
    expected_b = round(20 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == round(90 + expected_b, 2)


def test_total_without_coupon_or_shipping():
    c = Cart()
    c.add_item("BulkItem", 100, 100)  # bulk discount 15%
    # subtotal: 100*100*0.85=8500
    assert c.subtotal() == 8500.0
    # no coupon, subtotal>=1000 so free shipping
    assert c.total() == 8500.0


def test_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("SmallItem", 10, 2)   # no bulk discount -> 20
    # apply coupon 10%
    amount_after_coupon = round(20 * (1 - 0.10), 2)
    expected_total = round(amount_after_coupon + shipping_fee(amount_after_coupon), 2)
    assert c.total(coupon="SAVE10") == expected_total

# Edge case: empty cart no shipping

def test_empty_cart_no_shipping():
    c = Cart()
    assert c.total() == 0
