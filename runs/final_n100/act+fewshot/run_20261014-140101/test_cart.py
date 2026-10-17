import pytest
import cart

# Helper for rounding comparison
def round2(x):
    return round(float(x), 2)

# ------------------- apply_discount -------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (50, -5),   # percent <0
    (50, 105),  # percent >100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------- bulk_discount_percent -------------------
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
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------- parse_coupon -------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAVE0",       # N <1
    "SAVE51",      # N >50
    "INVALID",     # wrong prefix
    "save-5",
    "",            
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------- shipping_fee -------------------
@pytest.mark.parametrize("subtotal,member,fee", [
    (1000, False, 0),
    (999.99, False, 60),
    (1200, True, 0),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------- Cart methods -------------------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # adding same item increments quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # different item
    c.add_item("banana", 0.5, 4)
    assert c.items() == {"apple": 5, "banana": 4}

@pytest.mark.parametrize("name,unit_price,quantity", [
    ("pear", -1, 2),
    ("pear", 1, -3),
    ("pear", 1, 0),
])
def test_cart_add_errors(name, unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

# Adding item with different price raises ValueError

def test_cart_add_different_price_error():
    c = cart.Cart()
    c.add_item("orange", 0.5, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 0.6, 1)

# ------------------- Cart.remove_item -------------------

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("tshirt", 10.0, 3)
    # remove fewer than quantity
    c.remove_item("tshirt", 2)
    assert c.items() == {"tshirt": 1}
    # remove remaining -> item removed
    c.remove_item("tshirt", 1)
    assert c.items() == {}

@pytest.mark.parametrize("name,quantity", [
    ("nonexistent", 1),
])
def test_cart_remove_nonexistent(name, quantity):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, quantity)

# Removing more than present leaves empty and removes item

def test_cart_remove_more_than_present():
    c = cart.Cart()
    c.add_item("hat", 5.0, 2)
    c.remove_item("hat", 5)  # should remove completely
    assert c.items() == {}

# ------------------- Cart.subtotal -------------------

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("widget", 20.0, 9)   # below bulk -> no discount
    assert round2(c.subtotal()) == 180.00
    c.add_item("widget", 20.0, 1)   # total 10 -> 5% bulk discount on this item
    # subtotal: (10*20)*0.95 = 190.0
    assert round2(c.subtotal()) == 190.00

# Bulk discounts apply per item quantity only

def test_cart_subtotal_bulk_independent():
    c = cart.Cart()
    c.add_item("a", 10.0, 9)   # no discount
    c.add_item("b", 10.0, 1)   # total 10 -> 5% discount
    assert round2(c.subtotal()) == 190.00

# Empty cart subtotal zero

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert round2(c.subtotal()) == 0.0

# ------------------- Cart.total -------------------

def test_cart_total_no_coupon_member_free_shipping():
    c = cart.Cart()
    c.add_item("expensive", 500.0, 3)  # quantity 3 -> no bulk discount
    total = c.total(member=True)
    # subtotal 1500, free shipping, member but irrelevant
    assert round2(total) == 1500.00

# With coupon reduce before shipping

def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("toy", 100.0, 5)   # quantity 5 -> no bulk discount
    total_before = c.subtotal()   # 500
    total_after = c.total(coupon="SAVE10")  # 10% off before shipping
    expected = 500 * 0.9 + 60  # subtotal after coupon, then shipping fee (not member)
    assert round2(total_after) == round2(expected)

# Coupon invalid raises ValueError

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Empty cart total zero, no shipping

def test_cart_total_empty():
    c = cart.Cart()
    assert round2(c.total()) == 0.0
