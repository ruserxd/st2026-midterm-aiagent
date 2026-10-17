import pytest
import cart

# Helper to round floats exactly as spec (two decimals)

def round2(x):
    return round(x, 2)

# ---------- apply_discount -------------------------------------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_percent_invalid_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# ---------- parse_coupon -----------------------------------------------------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEX",  # missing number
    "SAVE0",  # out of range
    "SAVE51",
    "INVALID10",
    "sAvE-5",
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (5000, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", unit_price=10, quantity=5)   # subtotal before discount: 50
    # quantity < 10 => no bulk discount -> 50
    assert round2(c.subtotal()) == 50.0
    # add more apples same price
    c.add_item("apple", unit_price=10, quantity=6)
    # total qty =11 -> bulk discount 5% => 55 * 0.95 = 52.25
    assert round2(c.subtotal()) == 52.25

    # add different item with bulk discount
    c.add_item("banana", unit_price=20, quantity=10)
    # banana subtotal: 200 * 0.95 = 190
    # total after apples: 52.25 + 190 = 242.25
    assert round2(c.subtotal()) == 242.25

def test_add_item_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("apple", unit_price=-5, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("apple", unit_price=5, quantity=0)
    # price mismatch
    c.add_item("orange", unit_price=3, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("orange", unit_price=4, quantity=1)

def test_remove_item_and_auto_remove():
    c = cart.Cart()
    c.add_item("tshirt", unit_price=30, quantity=3)
    c.remove_item("tshirt", quantity=2)  # qty left 1
    assert c.items() == {"tshirt": 1}
    c.remove_item("tshirt", quantity=1)  # should remove
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

def test_total_without_coupon_and_membership():
    c = cart.Cart()
    c.add_item("item", unit_price=100, quantity=1)  # subtotal 100
    # total = 100 + shipping fee 60 => 160
    assert round2(c.total()) == 160.0

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", unit_price=200, quantity=1)  # subtotal 200
    # coupon SAVE10 -> reduce 10% => 180
    # shipping fee on 180 for member: half of 60 =30
    assert round2(c.total(member=True, coupon="SAVE10")) == 210.0

# Test that invalid coupon propagates error

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
