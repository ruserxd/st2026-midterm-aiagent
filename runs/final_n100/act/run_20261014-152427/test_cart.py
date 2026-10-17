import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Test apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("percent", [0, 100])
def test_apply_discount_percent_bounds(percent):
    val = round(123.45 * (1 - percent / 100), 2)
    assert apply_discount(123.45, percent) == val

with pytest.raises(ValueError):
    apply_discount(100, -5)
with pytest.raises(ValueError):
    apply_discount(100, 105)

with pytest.raises(ValueError):
    apply_discount(-1, 10)

# ---------- Test shipping_fee ----------

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

assert shipping_fee(200, member=True) == 30
assert shipping_fee(1200, member=True) == 0

with pytest.raises(ValueError):
    shipping_fee(-10)

# ---------- Test bulk_discount_percent ----------

def test_bulk_discount_percent_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(250) == 15

with pytest.raises(ValueError):
    bulk_discount_percent(0)
with pytest.raises(ValueError):
    bulk_discount_percent(-5)

# ---------- Test parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("  SAVE50  ") == 50

for bad in ["", "SAVE0", "SAVEX5", "DISCOUNT10", "SAVE101"]:
    with pytest.raises(ValueError):
        parse_coupon(bad)

# ---------- Test Cart class ----------

def test_cart_empty_total():
    cart = Cart()
    assert cart.total() == 0
    assert cart.subtotal() == 0

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=2)
    c.add_item("banana", unit_price=50)
    assert c.items() == {"apple": (100, 2), "banana": (50, 1)}
    assert c.subtotal() == 250

def test_cart_remove_item():
    c = Cart()
    c.add_item("item", unit_price=20, quantity=5)
    c.remove_item("item", quantity=3)
    assert c.items()["item"] == (20, 2)
    with pytest.raises(KeyError):
        c.remove_item("item", quantity=5)

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("widget", unit_price=500, quantity=1)
    # subtotal 500, coupon SAVE10 -> 450
    assert c.total(coupon="SAVE10") == pytest.approx(510.0)

def test_cart_total_member_and_bulk_discount():
    c = Cart()
    c.add_item("gadget", unit_price=200, quantity=120)
    discounted_subtotal = apply_discount(24000, 15)
    assert c.total(member=True) == round(discounted_subtotal, 2)

def test_cart_invalid_coupon():
    c = Cart()
    c.add_item("item", unit_price=100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
