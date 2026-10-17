import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

# rounding behavior
@ pytest.mark.parametrize("price,percent,expected",[
    (10, 33, 6.7),  # 10 * 0.67 = 6.7
    (9, 11, 8.01),   # 9 * 0.89 = 8.01
])
def test_apply_discount_rounding(price, percent, expected):
    assert apply_discount(price, percent) == expected

# error cases
with pytest.raises(ValueError):
    apply_discount(-1, 10)
with pytest.raises(ValueError):
    apply_discount(100, -5)
with pytest.raises(ValueError):
    apply_discount(100, 110)

# ---------- bulk_discount_percent ------------------------------------
def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

with pytest.raises(ValueError):
    bulk_discount_percent(0)
with pytest.raises(ValueError):
    bulk_discount_percent(-5)
# non-integer
with pytest.raises(ValueError):
    bulk_discount_percent(10.5)

# ---------- parse_coupon --------------------------------------------
def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon(" SAVE30") == 30

with pytest.raises(ValueError):
    parse_coupon("SAV10")  # missing 'E'
with pytest.raises(ValueError):
    parse_coupon("SAVE0")   # below min
with pytest.raises(ValueError):
    parse_coupon("SAVE51")  # above max
with pytest.raises(ValueError):
    parse_coupon("ABC10")

# ---------- shipping_fee --------------------------------------------
def test_shipping_fee():
    assert shipping_fee(1000) == 0.0
    assert shipping_fee(1500) == 0.0
    assert shipping_fee(999.99) == 60.0
    assert shipping_fee(500, member=True) == 30.0
    assert shipping_fee(2000, member=False) == 0.0

with pytest.raises(ValueError):
    shipping_fee(-5)

# ---------- Cart functionality ---------------------------------------
def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # add same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}
    # adding different unit price should raise
    with pytest.raises(ValueError):
        c.add_item("apple", 2.00, 1)

# ---------- Cart removal --------------------------------------------
def test_cart_remove():
    c = Cart()
    c.add_item("banana", 0.5, 4)
    c.remove_item("banana")
    assert c.items() == {"banana": 3}
    # remove more than existing quantity removes item
    c.remove_item("banana", 5)
    assert "banana" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("orange")

# ---------- subtotal calculation -------------------------------------
def test_cart_subtotal():
    c = Cart()
    c.add_item("itemA", 10.0, 9)   # no discount
    assert c.subtotal() == 90.0
    c.add_item("itemB", 5.0, 15)  # bulk discount 5%
    # itemB: 5*15=75 -> 5% off = 71.25
    expected = round(90.0 + 71.25, 2)
    assert c.subtotal() == expected

# ---------- total calculation ----------------------------------------
def test_cart_total_no_coupon():
    c = Cart()
    c.add_item("widget", 20.0, 1)   # subtotal 20
    # subtotal<1000, non-member -> shipping 60
    assert c.total() == round(20 + 60, 2)

# coupon application and shipping on discounted amount

def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("expensive", 2000.0, 1)   # subtotal 2000 -> free shipping
    assert c.total(member=True, coupon="SAVE10") == round(2000 * 0.9, 2)

# empty cart returns zero

def test_cart_total_empty():
    c = Cart()
    assert c.total() == 0.0
    assert c.total(coupon="SAVE20") == 0.0
