import pytest
import cart

# --- Discount and Shipping Functions Tests ---

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (123.456, 5),
    (50, 100),
])
def test_apply_discount_various(price, percent):
    expected = round(price * (1 - percent / 100), 2)
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 20),  # negative price
    (10, -5),   # negative percent
    (10, 105),  # percent >100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (101, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVExx",
    "SAVE-10",
    "",
    "   ",
    "ABCD",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (800, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart tests ----

def test_cart_add_item_new():
    c = cart.Cart()
    c.add_item("Apple", 2.5, quantity=3)
    assert c.items() == {"Apple": 3}

def test_cart_add_same_item_increase_quantity():
    c = cart.Cart()
    c.add_item("Banana", 1.0, quantity=4)
    c.add_item("Banana", 1.0, quantity=2)
    assert c.items() == {"Banana": 6}

def test_cart_add_same_name_different_price_error():
    c = cart.Cart()
    c.add_item("Orange", 1.5, quantity=3)
    with pytest.raises(ValueError):
        c.add_item("Orange", 2.0, quantity=1)

def test_cart_add_negative_unit_price_error():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Apple", -1.0, quantity=1)

def test_cart_add_zero_unit_price_allowed():
    c = cart.Cart()
    c.add_item("ZeroPrice", 0.0, quantity=2)
    assert c.items() == {"ZeroPrice": 2}

@pytest.mark.parametrize("quantity", [0, -1])
def test_cart_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Apple", 1.0, quantity=quantity)

def test_cart_remove_decrease_and_removal():
    c = cart.Cart()
    c.add_item("Banana", 1.0, quantity=5)
    c.remove_item("Banana", quantity=2)
    assert c.items() == {"Banana": 3}
    c.remove_item("Banana", quantity=3)  # remove remaining
    assert c.items() == {}

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("Apple")

def test_cart_remove_more_than_available():
    c = cart.Cart()
    c.add_item("Orange", 1.0, quantity=1)
    c.remove_item("Orange", quantity=5)   # should remove
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("Orange")

def test_cart_items_returns_dict():
    c = cart.Cart()
    c.add_item("A", 1.0, quantity=2)
    c.add_item("B", 3.0, quantity=4)
    assert c.items() == {"A": 2, "B": 4}

# Subtotal tests

def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("Apple", 10.0, quantity=3)
    assert c.subtotal() == round(10.0 * 3, 2)

def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("Banana", 5.0, quantity=12)  # 5% discount
    expected = round(5.0 * 12 * (1 - 0.05), 2)
    assert c.subtotal() == expected

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("Apple", 3.0, quantity=15)   # 5% discount
    c.add_item("Orange", 4.0, quantity=8)   # no discount
    exp1 = round(3.0 * 15 * (1 - 0.05), 2)
    exp2 = round(4.0 * 8, 2)
    assert c.subtotal() == round(exp1 + exp2, 2)

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

# Total tests

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("Apple", 10.0, quantity=2)   # subtotal 20
    expected = round(20 + 60, 2)
    assert c.total() == expected

def test_cart_total_coupon_non_member():
    c = cart.Cart()
    c.add_item("Apple", 10.0, quantity=2)
    discounted = round(20 * (1 - 0.10), 2)
    expected = round(discounted + 60, 2)
    assert c.total(coupon="SAVE10") == expected

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("Apple", 10.0, quantity=2)
    expected = round(20 + 30, 2)
    assert c.total(member=True) == expected

def test_cart_total_coupon_member():
    c = cart.Cart()
    c.add_item("Apple", 10.0, quantity=2)
    discounted = round(20 * (1 - 0.10), 2)
    expected = round(discounted + 30, 2)
    assert c.total(member=True, coupon="SAVE10") == expected

def test_cart_total_bulk_discount_coupon_member():
    c = cart.Cart()
    c.add_item("Banana", 5.0, quantity=12)   # bulk discount 5%
    subtotal = round(5.0 * 12 * (1 - 0.05), 2)
    discounted = round(subtotal * (1 - 0.20), 2)
    expected = round(discounted + 30, 2)
    assert c.total(member=True, coupon="SAVE20") == expected

def test_cart_total_free_shipping_above_1000():
    c = cart.Cart()
    c.add_item("Expensive", 10.0, quantity=200)   # bulk discount 15%
    subtotal = round(10.0 * 200 * (1 - 0.15), 2)
    assert c.total() == subtotal

def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True, coupon="SAVE10") == 0

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALIDCODE")
