import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1,10),(100,-5),(50,110)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("   SaVe30   ") == 30

@pytest.mark.parametrize("code", ["SAVEX", "10SAVE", "SAVE0", "SAVE51", "SAVE-5", "SA VE10", "SAVED"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert shipping_fee(1000, member=False) == 0
    assert shipping_fee(1001, member=False) == 0
    assert shipping_fee(999, member=False) == 60
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_empty_total():
    c = Cart()
    assert c.total() == 0

def test_cart_subtotal_and_add_remove():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=3)
    c.add_item("banana", unit_price=50)
    assert c.subtotal() == 350  # 3*100 + 1*50
    c.remove_item("apple", quantity=1)
    assert c.subtotal() == 250  # 2*100 + 50

@pytest.mark.parametrize(
    "items,expected_total",
    [
        ([("item", 500)], 560),   # subtotal 500, shipping 60
        ([("item", 2000)], 2000),  # free shipping
    ],
)
def test_cart_total_without_coupon(items, expected_total):
    c = Cart()
    for name, price in items:
        c.add_item(name, unit_price=price)
    assert c.total() == expected_total

@pytest.mark.parametrize(
    "items,coupon,expected",
    [
        ([("item", 200)], "SAVE10", 240),   # subtotal 200 -10% =180; + shipping60 =240
    ],
)
def test_cart_total_with_coupon(items,coupon,expected):
    c=Cart()
    for name,price in items:
        c.add_item(name,unit_price=price)
    assert c.total(coupon=coupon)==expected

@pytest.mark.parametrize(
    "items,coupon,member,expected",
    [
        ([("item",200)], None, True, 230),   # subtotal200 + member shipping30 =230
    ],
)
def test_cart_total_member_shipping(items,coupon,member,expected):
    c=Cart()
    for name,price in items:
        c.add_item(name,unit_price=price)
    assert c.total(member=member)==expected
