import pytest
import cart

# --- apply_discount -------------------------------------------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full price reduction
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-10, 20),          # negative price
    (50, -5),           # negative percent
    (50, 105),          # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent -------------------------------------------------

@pytest.mark.parametrize("quantity,percent", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ----------------------------------------------------------

@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAV10",          # missing S
    "SAVE51",         # >50
    "save0",          # <1
    "12345",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ----------------------------------------------------------

@pytest.mark.parametrize("subtotal,member,result", [
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart ------------------------------------------------------------

def test_cart_init_and_items_empty():
    c = cart.Cart()
    assert c.items() == {}

# adding items

def test_add_item_new_and_existing():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # add same item with same price increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}

# adding invalid data

def test_add_item_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, 1)          # negative price
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, 0)           # non‑positive quantity
    with pytest.raises(ValueError):
        c.add_item("pear", 2.0, "two")        # non‑int quantity
    # price mismatch when item exists
    c.add_item("grape", 3.0, 1)
    with pytest.raises(ValueError):
        c.add_item("grape", 4.0, 1)

# removing items

def test_remove_item():
    c = cart.Cart()
    c.add_item("kiwi", 2.5, 4)
    c.remove_item("kiwi", 2)
    assert c.items() == {"kiwi": 2}
    # remove remaining quantity -> item removed
    c.remove_item("kiwi", 2)
    assert c.items() == {}

# removing non‑existent item raises KeyError

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("mango", 1)

# subtotal calculations with bulk discounts

def test_subtotal_basic_and_discount():
    c = cart.Cart()
    # 5 apples at $10 each: no discount (quantity <10)
    c.add_item("apple", 10.0, 5)
    assert c.subtotal() == 50.00
    # 12 bananas at $2 each: quantity>=10 => 5% bulk discount per item
    c.add_item("banana", 2.0, 12)
    banana_total = 2.0 * 12 * (1 - 0.05)  # 24 * 0.95
    assert c.subtotal() == round(50 + banana_total, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200.0, 1)   # subtotal $200
    # No bulk discount
    subtotal = 200.00
    # Apply coupon SAVE10 => 10% off subtotal
    after_coupon = cart.apply_discount(subtotal, 10)
    assert after_coupon == 180.0
    # Shipping fee: not member, subtotal <1000 => 60
    shipping = cart.shipping_fee(after_coupon)
    assert shipping == 60
    total_expected = round(after_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == total_expected

# total for empty cart returns 0 (no shipping)

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# invalid coupon in total raises ValueError

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
