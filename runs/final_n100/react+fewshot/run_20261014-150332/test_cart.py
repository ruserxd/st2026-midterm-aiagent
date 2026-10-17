import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.0),
    (100, 50, 50.0),
])
def test_apply_discount_edge(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save15 ") == 15
    assert parse_coupon("SaVe1") == 1

@pytest.mark.parametrize("code", ["", "ABCD", "SAVE0", "SAVE51", "SAVEXY", "S AVE10"])   # malformed or out of range
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60.0
    assert shipping_fee(999.99) == 60.0
    assert shipping_fee(1000) == 0.0
    assert shipping_fee(2000) == 0.0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ------------------------------------------------------

def test_cart_initially_empty():
    c = Cart()
    assert list(c.items()) == []  # empty dict, no items
    assert c.subtotal() == 0.00
    assert c.total() == 0.00

def test_add_and_remove_item_basic():
    c = Cart()
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == 4.50  # no bulk discount yet
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 1}
    assert c.subtotal() == 1.50
    c.remove_item("apple", 1)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("banana")

@pytest.mark.parametrize(
    "quantity,expected_discount",
    [(9, 0), (10, 5), (49, 5), (50, 10), (100, 15)],
)
def test_subtotal_bulk_discount(quantity, expected_discount):
    c = Cart()
    c.add_item("widget", 20.00, quantity)
    # calculate expected
    discount_percent = bulk_discount_percent(quantity)
    discounted_price_per_unit = apply_discount(20.00, discount_percent)
    expected_subtotal = round(discounted_price_per_unit * quantity, 2)
    assert c.subtotal() == expected_subtotal

def test_add_item_same_name_different_price_raises():
    c = Cart()
    c.add_item("soda", 1.00)
    with pytest.raises(ValueError):
        c.add_item("soda", 1.50)  # price mismatch

@pytest.mark.parametrize(
    "unit_price,quantity",
    [(-5, 1), (5, -2), (5, 0)],
)
def test_add_item_invalid_parameters_raises(unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("item", unit_price, quantity)

# ---------- total calculations ----------------------------------------------

def test_total_with_coupon_and_shipping():
    # Items worth 400 with no bulk discount
    cart = Cart()
    cart.add_item("book", 100.00, 4)  # 4 units => 5% discount per unit
    # Bulk discount applies to each unit: 95% of 100 = 95 -> subtotal 380.0
    assert cart.subtotal() == 380.0
    # Apply coupon SAVE10
    total_with_coupon = cart.total(coupon="SAVE10")
    # After coupon: 380 - 38 = 342.0
    # Shipping fee for non-member on 342 -> 60 (subtotal <1000)
    expected_total = round(342.0 + 60.0, 2)
    assert total_with_coupon == expected_total

def test_total_member_free_shipping():
    cart = Cart()
    cart.add_item("expensive", 2000.00, 1)  # no bulk discount
    # subtotal 2000
    total_member = cart.total(member=True)
    # coupon none, shipping free (>=1000)
    assert total_member == 2000.00

@pytest.mark.parametrize("coupon_code", ["INVALID", "SAVE60"])   # invalid codes
def test_total_invalid_coupon_raises(coupon_code):
    cart = Cart()
    cart.add_item("pen", 5, 2)
    with pytest.raises(ValueError):
        cart.total(coupon=coupon_code)

# ---------- total empty cart no shipping -----------------------------------

def test_total_empty_cart_no_shipping():
    c = Cart()
    assert c.total() == 0.00
