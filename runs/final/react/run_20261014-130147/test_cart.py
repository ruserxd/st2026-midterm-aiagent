import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ---------------------------

def test_bulk_discount_ranges():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -3, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save15 ") == 15
    assert parse_coupon("SaVe50") == 50

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "DISCOUNT10", "SA VE10", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0

def test_shipping_fee_member():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart ---------------------------------------------

def test_cart_add_and_remove():
    c = Cart()
    c.add_item("apple", 100, quantity=3)
    assert c.items() == {"apple": (100, 3)}
    # add same item increments quantity
    c.add_item("apple", 100, quantity=2)
    assert c.items()["apple"] == (100, 5)
    # remove partially
    c.remove_item("apple", quantity=1)
    assert c.items()["apple"] == (100, 4)
    # remove all remaining
    c.remove_item("apple", quantity=4)
    assert "apple" not in c.items()

def test_cart_subtotal_and_total():
    c = Cart()
    c.add_item("item1", 200, quantity=2)   # subtotal 400
    c.add_item("item2", 300, quantity=1)   # subtotal 700
    assert c.subtotal() == 700
    # total without member or coupon: shipping 60 + subtotal 700 = 760
    assert c.total() == 760
    # with member discount 5% and half shipping
    expected_total_member = round((c.subtotal()*0.95)+30,2)
    assert c.total(member=True) == expected_total_member
    # apply coupon SAVE10 (10%) to subtotal before shipping
    total_with_coupon = round(c.subtotal()*0.9 + 60,2)
    assert c.total(coupon="SAVE10") == total_with_coupon
    # member and coupon together
    total_mem_coup = round(c.subtotal()*0.85 + 30,2)
    assert c.total(member=True, coupon="save5") == total_mem_coup

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("item", 100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
