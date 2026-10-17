import pytest
import cart

# Helper to create a cart with items for tests

def make_cart(items):
    c = cart.Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary checks for ValueError
@pytest.mark.parametrize("price,percent", [
    (-1, 10),     # negative price
    (100, -5),    # negative percent
    (100, 105),   # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),      # below 10
    (10, 5),     # start of 10+ tier
    (49, 5),     # just before 50
    (50, 10),    # start of 50+ tier
    (99, 10),    # just before 100
    (100, 15),   # start of 100+ tier
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# negative or zero quantity should error
@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_error(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,percent", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon(code, percent):
    assert cart.parse_coupon(code) == percent

# invalid coupon codes
@pytest.mark.parametrize("code", [
    "",
    "SAVEXX",
    "SAVE0",
    "SAVE51",
    "  ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# negative subtotal error
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class methods ----------

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

@pytest.mark.parametrize("name,unit_price,qty", [
    ("apple", 1.5, 2),
    ("banana", 0.75, 5),
])
def test_add_item(name, unit_price, qty):
    c = cart.Cart()
    c.add_item(name, unit_price, qty)
    assert c.items()[name] == qty
    # adding same item increases quantity only if price matches
    c.add_item(name, unit_price, 3)
    assert c.items()[name] == qty + 3

# error when prices differ

def test_add_item_different_price():
    c = cart.Cart()
    c.add_item("apple", 1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)

# remove_item tests

def test_remove_item_basic():
    c = cart.Cart()
    c.add_item("pear", 2.0, 5)
    c.remove_item("pear", 3)
    assert c.items()["pear"] == 2

def test_remove_item_entire_and_above():
    c = cart.Cart()
    c.add_item("melon", 3.0, 4)
    c.remove_item("melon", 5)  # should remove the item entirely
    assert "melon" not in c.items()

# removing non-existent key raises KeyError

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk_discount():
    # item A: 10 units, price 2 => bulk discount 5%
    # subtotal for A before discount = 20, after 5% = 19.0
    c = cart.Cart()
    c.add_item("A", 2.0, 10)
    assert c.subtotal() == 19.00

# subtotal with multiple items and mixed discounts

def test_subtotal_multiple_items():
    # A: 5 units (no discount) -> 5*1=5
    # B: 12 units => 5% discount on 12 -> unit 3? Actually we calculate discount per quantity for that item
    c = cart.Cart()
    c.add_item("A", 1.0, 5)
    c.add_item("B", 2.0, 12)  # 5% discount
    # A subtotal: 5
    # B subtotal before discount: 24, after 5% => 22.8
    assert c.subtotal() == round(5 + 22.8, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 1000.0, 1)   # subtotal 1000, no bulk discount
    # apply a 10% coupon: amount becomes 900
    assert c.total(coupon="SAVE10") == 930.00  # 900 + 30 shipping for member? Wait member default False -> 60 shipping because > 1000? Actually subtotal after coupon is 900 < 1000, so 60 shipping

# total when cart empty should be zero and no shipping

def test_total_empty_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
