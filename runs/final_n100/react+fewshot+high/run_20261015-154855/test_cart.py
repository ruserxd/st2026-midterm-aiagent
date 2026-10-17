import pytest
import cart

# --- apply_discount tests ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (50, 0, 50.0),
    (120, 100, 0.0),
    (10.555, 5, 10.03),  # rounding to two decimals
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # spec: >=50 -> 10
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [
    0,
    -1,
    3.5,
    "ten",
])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save10", 10),   # case-insensitive per spec, but implementation is case-sensitive -> will fail
    ("  SAVE25  ", 25),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVEXX",
    "12345",
    "XYZ10",
    None,
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1, False)

@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
    (300, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# --- Cart class tests ---
def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_cart_add_and_remove():
    c = cart.Cart()
    c.add_item("apple", 10, 2)
    assert c.items() == {"apple": 2}
    # Add same item with same price
    c.add_item("apple", 10, 3)
    assert c.items()["apple"] == 5
    # Adding same name with different unit_price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 12, 1)
    # Remove some quantity
    c.remove_item("apple", 3)
    assert c.items()["apple"] == 2
    # Removing all quantity should remove item (bug in implementation)
    c.remove_item("apple", 2)
    assert "apple" not in c.items()
    # Removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("banana", 1)

def test_cart_remove_more_than_existing():
    c = cart.Cart()
    c.add_item("banana", 5, 2)
    c.remove_item("banana", 10)   # more than existing
    assert "banana" not in c.items()

def test_items_return_copy():
    c = cart.Cart()
    c.add_item("orange", 7, 3)
    items_copy = c.items()
    items_copy["orange"] = 999
    # internal state should remain unchanged
    assert c.items()["orange"] == 3

def test_cart_subtotal_with_bulk_discounts():
    c = cart.Cart()
    c.add_item("A", 100, 5)
    c.add_item("B", 200, 15)
    c.add_item("C", 150, 55)
    assert c.subtotal() == 10775.0

def test_cart_total_without_coupon_or_member():
    c = cart.Cart()
    c.add_item("A", 100, 5)
    c.add_item("B", 200, 15)
    c.add_item("C", 150, 55)
    expected_subtotal = 10775.0
    assert c.total() == expected_subtotal

def test_cart_total_with_coupon_only():
    c = cart.Cart()
    c.add_item("A", 100, 5)
    c.add_item("B", 200, 15)
    c.add_item("C", 150, 55)
    sub = 10775.0
    discounted = cart.apply_discount(sub, 10)  # 10% off
    expected_total = discounted + cart.shipping_fee(discounted, False)
    assert c.total(coupon="SAVE10") == expected_total

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("A", 100, 5)
    c.add_item("B", 200, 15)
    c.add_item("C", 150, 55)
    sub = 10775.0
    discounted = cart.apply_discount(sub, 10)  # 10% off
    expected_total = discounted + cart.shipping_fee(discounted, True)
    assert c.total(member=True, coupon="SAVE10") == expected_total

def test_cart_total_with_coupon_affecting_shipping():
    c = cart.Cart()
    c.add_item("expensive", 1300, 1)   # subtotal 1300
    discounted = cart.apply_discount(1300.0, 50)  # 50% off -> 650
    expected_total_spec = discounted + cart.shipping_fee(discounted, False)
    assert c.total(coupon="SAVE50") == expected_total_spec

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("A", 100, 5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALIDCODE")
