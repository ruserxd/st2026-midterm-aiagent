import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

def r(v):
    return round(v, 2)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1,10), (10,-5), (10,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon(" SAVE15 ") == 15

@pytest.mark.parametrize("code", ["SAVEBAD", "SA0", "ABCD", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200, member=False) == 0

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart methods ----------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, quantity=2)
    assert c.items() == {"apple": 2}
    # Add more of same item (exact same name)
    c.add_item("apple", 1.0, quantity=3)
    assert c.items() == {"apple": 5}


def test_cart_add_invalid_price_quantity():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, quantity=0)


def test_cart_add_conflicting_price():
    c = Cart()
    c.add_item("pear", 2.5)
    with pytest.raises(ValueError):
        c.add_item("pear", 3.0)


def test_cart_remove_and_items():
    c = Cart()
    c.add_item("orange", 1.0, quantity=4)
    c.remove_item("orange", quantity=2)
    assert c.items() == {"orange": 2}
    c.remove_item("orange", quantity=2)
    assert c.items() == {}


def test_cart_remove_nonexistent():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("mango")

# ---------- subtotal calculation ----------

def test_subtotal_no_discount():
    c = Cart()
    c.add_item("item", 10.0, quantity=3)
    assert r(c.subtotal()) == 30.00


def test_subtotal_bulk_discounts():
    c = Cart()
    c.add_item("small", 2.0, quantity=9)
    c.add_item("medium", 5.0, quantity=10)
    expected = 18 + (5 * 10 * 0.95)
    assert r(c.subtotal()) == round(expected,2)

# ---------- total calculation with coupon and shipping ----------

def test_total_no_coupon():
    c = Cart()
    c.add_item("item", 100.0, quantity=1)
    assert r(c.total()) == 160.00


def test_total_with_coupon_and_member_shipping():
    c = Cart()
    c.add_item("item", 200.0, quantity=1)
    assert r(c.total(member=True, coupon="SAVE20")) == 190.00


def test_total_invalid_coupon():
    c = Cart()
    c.add_item("item", 50.0)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- empty cart total ----------

def test_empty_cart_total_zero():
    c = Cart()
    assert r(c.total()) == 0.00
