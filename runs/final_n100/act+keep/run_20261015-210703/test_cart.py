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

@ pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [-1, 0, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("  save20 ") == 20

@ pytest.mark.parametrize(
    "code",
    ["", "ABCD", "SAVE0", "SAVE51", "SAVE-5", "save50extra"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60

with pytest.raises(ValueError):
    shipping_fee(-1)

# ---------- Cart class basic functionality ----------

def test_cart_add_and_items():
    c = Cart()
    c.add_item("apple", unit_price=2, quantity=3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity but requires same price
    c.add_item("apple", unit_price=2, quantity=2)
    assert c.items() == {"apple": 5}
    with pytest.raises(ValueError):
        c.add_item("apple", unit_price=3, quantity=1)  # different price

# ---------- Cart remove and emptying ----------

def test_cart_remove_and_empty():
    c = Cart()
    c.add_item("banana", unit_price=1, quantity=5)
    c.remove_item("banana", quantity=2)
    assert c.items() == {"banana": 3}
    # removing more than remaining should remove entirely
    c.remove_item("banana", quantity=10)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# ---------- subtotal bulk discount effect ----------

def test_cart_subtotal_bulk_discount():
    c = Cart()
    # 9 units: no discount
    c.add_item("item", unit_price=10, quantity=9)
    assert c.subtotal() == 90.0
    # reset cart
    c = Cart()
    c.add_item("item", unit_price=10, quantity=10)
    # bulk discount 5%: 10*10=100 -> 95
    assert c.subtotal() == 95.0
    # 50 units: 10% off
    c = Cart()
    c.add_item("item", unit_price=20, quantity=50)
    assert c.subtotal() == 20 * 50 * 0.90  # 900

# ---------- total with coupon and shipping ----------

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("item", unit_price=100, quantity=1)
    subtotal = c.subtotal()  # no bulk discount -> 100
    assert subtotal == 100.0
    # No coupon: total = subtotal + shipping (60) = 160
    assert c.total() == 160.0
    # Member: shipping half 30, so total 130
    assert c.total(member=True) == 130.0
    # Coupon 20% reduces subtotal to 80, shipping 60 -> 140
    assert c.total(coupon="SAVE20") == 140.0
    # Empty cart: cost 0
    empty = Cart()
    assert empty.total() == 0.0

# ---------- rounding behavior and error propagation ----------

def test_cart_total_rounding_and_errors():
    c = Cart()
    c.add_item("item", unit_price=1, quantity=3)
    # subtotal 3 -> no shipping (free above 1000) so total 3
    assert c.total() == 3.0
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
