import re
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper assertions for rounding and value errors ---------

def assert_value_error(callable_obj, *args, **kwargs):
    """Assert that the callable raises ValueError with given args."""
    with pytest.raises(ValueError):
        callable_obj(*args, **kwargs)

# ---------- apply_discount tests ------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # percent boundaries
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

# price negative should raise ValueError
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    assert_value_error(apply_discount, price, 10)

# percent outside 0-100 raises ValueError
@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_invalid(percent):
    assert_value_error(apply_discount, 50, percent)

# ---------- bulk_discount_percent tests -----------------------------

def test_bulk_discount_percent_cases():
    # quantity thresholds
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

# quantity must be positive integer
@pytest.mark.parametrize("qty", [0, -5, 3.7])
def test_bulk_discount_percent_invalid(qty):
    assert_value_error(bulk_discount_percent, qty)

# ---------- parse_coupon tests -------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE25 ") == 25

@pytest.mark.parametrize("code", ["",
                                    "SAVEXX",
                                    "save0",
                                    "SAVE51",
                                    " SAVE-5 ",
                                    "  save 10  "])
def test_parse_coupon_invalid(code):
    assert_value_error(parse_coupon, code)

# ---------- shipping_fee tests --------------------------------------

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

# member pays half of the fee
@pytest.mark.parametrize("subtotal", [0, 200, 950])
def test_shipping_fee_member(subtotal):
    assert shipping_fee(subtotal, member=True) == 30

# subtotal negative raises ValueError
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_subtotal_negative(subtotal):
    assert_value_error(shipping_fee, subtotal)

# ---------- Cart tests -----------------------------------------------

def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 2.5, quantity=3)  # total 7.5
    assert c.items() == {"apple": 3}
    assert c.subtotal() == 7.5
    c.add_item("banana", 1.0)
    assert c.items() == {"apple": 3, "banana": 1}
    # adding existing item increases quantity
    c.add_item("apple", 2.5, quantity=2)
    assert c.items()["apple"] == 5
    # trying to add with different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0, quantity=1)

def test_cart_remove_items():
    c = Cart()
    c.add_item("orange", 1.5, quantity=4)
    c.remove_item("orange", quantity=2)
    assert c.items()["orange"] == 2
    # remove all remaining
    c.remove_item("orange", quantity=2)
    assert "orange" not in c.items()
    # removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("banana")

# bulk discount applied in subtotal
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (10, 5.0),  # unit price 1 -> 5 after bulk 5%
        (50, 45.0), # 10% of 50 = 5; 50-5=45
        (100, 85.0),# 15% of 100 = 15; 100-15=85
    ],
)
def test_cart_subtotal_bulk_discount(quantity, expected):
    c = Cart()
    unit_price = 1.0
    c.add_item("widget", unit_price, quantity=quantity)
    assert c.subtotal() == pytest.approx(expected, rel=1e-9)

# total with coupon and shipping
def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("gadget", 20.0, quantity=5)  # subtotal 100 -> no bulk discount (5 items => 5% off?) Actually bulk_discount_percent(5)=0
    # subtotal is 100
    total_no_coupon = c.total(member=False)
    assert total_no_coupon == pytest.approx(160.0)  # 100 + shipping 60
    total_member = c.total(member=True)
    assert total_member == pytest.approx(130.0)  # 100 + shipping 30
    # with coupon of 10%
    total_coupon = c.total(coupon="SAVE10")
    # subtotal after coupon: 90; shipping 60 => 150
    assert total_coupon == pytest.approx(150.0)
    # member with coupon
    total_member_coupon = c.total(member=True, coupon="save10")
    assert total_member_coupon == pytest.approx(120.0)  # 90 + 30

# invalid coupon raises ValueError
def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("thing", 5.0)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# empty cart costs 0 (no shipping)
def test_empty_cart_total_zero():
    c = Cart()
    assert c.total() == 0

# subtotal rounding to two decimals
def test_subtotal_rounding():
    c = Cart()
    # price that leads to fractional cents
    c.add_item("precious", 0.333, quantity=3)  # 0.999 -> rounded 1.00
    assert c.subtotal() == pytest.approx(1.00)
