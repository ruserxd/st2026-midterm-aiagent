import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_edges(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-1, 10),
    (50, -5),
    (50, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ----------------- bulk_discount_percent ---------------------------------

def test_bulk_discount_percent_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----------------- parse_coupon ---------------------------------

def test_parse_coupon_basic():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon(" SAVE50 ") == 50

@pytest.mark.parametrize("code", ["sav10", "SAVE0", "SAVE51", "123", "SAVE-5", "SAVEE5"])  # invalid patterns
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----------------- shipping_fee ---------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----------------- Cart class ---------------------------------

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# adding items
@pytest.mark.parametrize("name, unit_price, quantity", [
    ("apple", 1.00, 5),
])
def test_cart_add_item(name, unit_price, quantity):
    c = Cart()
    c.add_item(name, unit_price, quantity)
    assert c.items() == {name: quantity}

# adding same item increases qty and requires same price

def test_cart_add_same_item_increases_quantity():
    c = Cart()
    c.add_item("banana", 0.5, 2)
    c.add_item("banana", 0.5, 3)
    assert c.items() == {"banana": 5}

@pytest.mark.parametrize("name, price1, price2", [
    ("orange", 1.00, 1.20),
])
def test_cart_add_same_item_different_price(name, price1, price2):
    c = Cart()
    c.add_item(name, price1, 1)
    with pytest.raises(ValueError):
        c.add_item(name, price2, 1)

@pytest.mark.parametrize("unit_price, quantity", [(-1, 1), (0.5, 0), (0.5, -3)])
def test_cart_add_invalid(unit_price, quantity):
    with pytest.raises(ValueError):
        Cart().add_item("item", unit_price, quantity)

# removing items

def test_cart_remove_item():
    c = Cart()
    c.add_item("pen", 2.0, 3)
    c.remove_item("pen", 1)
    assert c.items() == {"pen": 2}
    c.remove_item("pen", 2)
    assert c.items() == {}

def test_cart_remove_nonexistent_raises():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexist", 1)

# subtotal calculations with bulk discounts

def test_cart_subtotal_with_bulk_discount():
    c = Cart()
    c.add_item("widget", 10.0, 9)   # <10 => no discount
    assert c.subtotal() == 90.0
    c.remove_item("widget")  # remove all
    c.add_item("widget", 10.0, 10)  # bulk >=10 => 5%
    assert c.subtotal() == apply_discount(100.0, 5)

# total with coupon and shipping

def test_cart_total_without_coupon():
    c = Cart()
    c.add_item("item", 200.0, 1)
    # subtotal 200 -> no bulk discount
    assert c.subtotal() == 200.0
    # shipping fee for 200 -> 60
    expected = apply_discount(200.0, 0) + 60
    assert c.total() == round(expected, 2)


def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("item", 200.0, 1)
    # coupon SAVE10 -> 10%
    total_after_coupon = apply_discount(200.0, 10)
    shipping = shipping_fee(total_after_coupon, member=True)  # should be 30
    expected_total = round(total_after_coupon + shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# total with free shipping threshold

def test_cart_total_free_shipping():
    c = Cart()
    c.add_item("expensive", 1000.0, 1)
    # subtotal 1000 -> no discount
    assert c.subtotal() == 1000.0
    # shipping fee free (subtotal >= 1000)
    assert c.total() == 1000.0

# invalid coupon

def test_cart_total_invalid_coupon_raises():
    c = Cart()
    c.add_item("item", 50.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# subtotal rounding to two decimals

def test_subtotal_rounding():
    c = Cart()
    # price 1.333..., quantity 3 => 4.0 after bulk discount? let's compute
    c.add_item("test", 1.333, 3)
    # no bulk discount; subtotal should be round(4.0,2)=4.0
    assert c.subtotal() == 4.0
