import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Helper to round to two decimals for comparison
round2 = lambda x: round(x, 2)

# --------- Tests for apply_discount ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize(
    "price, percent", [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --------- Tests for bulk_discount_percent ---------------------------

def test_bulk_discount_basic():
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize(
    "quantity", [0, -1, 2.5],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --------- Tests for parse_coupon -----------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25 ") == 25
    assert parse_coupon(" SAVE5") == 5
    # boundary values
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

@ pytest.mark.parametrize(
    "code", ["SAVE0", "SAVE51", "DISCOUNT10", "", "SAVExx", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --------- Tests for shipping_fee -----------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

@ pytest.mark.parametrize(
    "subtotal", [-1, -10],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --------- Tests for Cart class -------------------------------------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# Adding items, quantity accumulation, price validation

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", 10, 3)
    # bulk discount for 3 units -> 0%
    assert round2(c.subtotal()) == 30.0
    c.add_item("banana", 5, 10)  # 10% discount for 10 units
    # banana subtotal before discount: 50; after 10%: 45
    expected = 30 + 45
    assert round2(c.subtotal()) == expected

# test bulk discount thresholds

def test_cart_bulk_discount_thresholds():
    c = Cart()
    c.add_item("item", 20, 9)
    assert round2(c.subtotal()) == 180.0  # no discount
    c.remove_item("item", 4)  # now quantity=5 -> 0% discount still
    assert round2(c.subtotal()) == 100.0
    c.add_item("item", 20, 5)  # total 10 units -> 5%
    assert round2(c.subtotal()) == round2(200 * 0.95)

# test remove item and key error

def test_cart_remove_and_errors():
    c = Cart()
    c.add_item("apple", 10, 2)
    c.remove_item("apple", 1)
    assert c.items() == {"apple": 1}
    c.remove_item("apple", 1)  # should remove completely
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# test total calculation with coupon, shipping, member

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("item", 100, 5)   # subtotal 500, no bulk discount
    # apply coupon SAVE10 -> 450
    assert round2(c.total(coupon="SAVE10")) == round2(450 + shipping_fee(450))
    # member should halve shipping on that amount
    assert round2(c.total(member=True, coupon="SAVE10")) == round2(
        450 + shipping_fee(450, member=True)
    )

# test empty cart has no shipping

def test_cart_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0.0

# test invalid coupon in total

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
