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

@ pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_edges(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price, percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_limits():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

@ pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("  SaVe50") == 50
    assert parse_coupon(" SAVE1 ") == 1

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVExx", "NOTVALID", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0
    # member discount
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1500, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_initial_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_and_remove_item():
    c = Cart()
    c.add_item("apple", 2.5, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity, price must match
    c.add_item("apple", 2.5, 2)
    assert c.items() == {"apple": 5}
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0, 1)  # different price
    # remove part of quantity
    c.remove_item("apple", 4)
    assert c.items() == {"apple": 1}
    # remove remaining -> removed entirely
    c.remove_item("apple", 1)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("banana", 1)

@ pytest.mark.parametrize(
    "name, price, qty, expected",
    [
        ("item", 100.0, 1, 95.0),   # no bulk discount, 5% coupon
        ("bulk", 10.0, 15, 133.75),  # 5% bulk on 150 -> 142.5; then 5% coupon => 135.375
    ],
)
def test_cart_total_with_coupon(name, price, qty, expected):
    c = Cart()
    c.add_item(name, price, qty)
    result = c.total(coupon="SAVE5")
    assert round(result, 2) == round(expected, 2)

# Test shipping cost is applied after coupon reduction

def test_cart_shipping_after_coupon():
    c = Cart()
    # subtotal 2000, free shipping before discount, but apply coupon reduces amount
    c.add_item("expensive", 500.0, 5)  # 2500 total, bulk discount 15% => 2125
    total_before_coupon = c.total()   # no coupon, should include shipping? subtotal>1000 so free
    assert round(total_before_coupon, 2) == 2125.0
    # with coupon 10%: amount becomes 1912.5, still >1000 so free shipping
    total_with_coupon = c.total(coupon="SAVE10")
    assert round(total_with_coupon, 2) == 1912.5

# Edge case: empty cart has no shipping

def test_empty_cart_no_shipping():
    c = Cart()
    assert c.total() == 0.0
