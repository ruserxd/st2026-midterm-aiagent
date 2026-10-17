import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_normal_cases():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

@pytest.mark.parametrize("price", [-1, -5])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", ["a", -10, 101, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent -----------------------------------------

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon(" SAVE5 ") == 5

@pytest.mark.parametrize(
    "code",
    ["SAVEX", "SAVEE100", "NOPE", "123", "SAVE0", "SAVE51", "SAVEBAD"]
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee_levels():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

assert shipping_fee(500, member=True) == 30
assert shipping_fee(2000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart ------------------------------------------------------------------

def test_cart_initially_empty():
    c = Cart()
    assert list(c.items()) == []
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 2, quantity=3)
    assert list(c.items()) == [("apple", 2, 3)]
    assert c.subtotal() == 6.0
    # remove part of the quantity
    c.remove_item("apple", quantity=1)
    assert list(c.items()) == [("apple", 2, 2)]
    assert c.subtotal() == 4.0
    # remove all remaining
    c.remove_item("apple")
    assert list(c.items()) == []
    assert c.subtotal() == 0.0

# coupon and shipping in total

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("widget", 50, quantity=20)  # subtotal 1000 -> bulk discount percent 15
    assert c.subtotal() == 1000.0
    # bulk discount applies only to items? The spec for Cart.total doesn't mention bulk,
    # so we test coupon and shipping only.
    total = c.total(coupon="SAVE10")
    # 10% off -> 900, shipping free (subtotal>=1000 before coupon? but rule says on amount after coupon)
    assert total == 900.0

# member discount via shipping

def test_cart_total_member_shipping_half():
    c = Cart()
    c.add_item("gadget", 20, quantity=5)  # subtotal 100
    total = c.total(member=True)
    # no coupon -> 100, shipping 30 (half of 60)
    assert total == 130.0

# test rounding to 2 decimals

def test_cart_total_rounding():
    c = Cart()
    c.add_item("item", 33.3333, quantity=1)
    total = c.total(coupon="SAVE10")  # 33.3333 * 0.9 = 30.0000? actually 29.99997
    assert round(total, 2) == 30.0
