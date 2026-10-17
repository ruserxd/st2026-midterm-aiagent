import pytest
import cart

# ---------- helper for rounding check ---------

def round2(x):
    return round(float(x), 2)

# ----- apply_discount -----
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# negative price or invalid percent should raise ValueError
@pytest.mark.parametrize("price,percent", [
    (-10, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE50 ", 50),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVExx", "A10", "SAVE-5", " SAVE51 "])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart -----
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item: correct additions and quantity increase

def test_add_item_basic(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple": 3}
    # adding same item increases qty
    empty_cart.add_item("apple", 1.0, 2)
    assert empty_cart.items() == {"apple": 5}

# unit_price mismatch raises ValueError

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("banana", 0.5, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 0.6, 2)

# invalid price or quantity raises ValueError
@pytest.mark.parametrize("price,quantity", [(-1,1),(0.5,-3)])
def test_add_item_errors(empty_cart, price, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", price, quantity)

# remove_item: reduce qty and delete when zero

def test_remove_item_basic():
    c = cart.Cart()
    c.add_item("orange", 0.8, 4)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 2}
    c.remove_item("orange", 2)  # should remove
    assert c.items() == {}

# removing non-existent item raises KeyError

def test_remove_item_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal calculation including bulk discounts

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 12 units, unit price $10 -> bulk discount 5%
    c.add_item("widget", 10.0, 12)
    expected_subtotal = round2(10.0 * 12 * (1 - 0.05))
    assert c.subtotal() == expected_subtotal

# subtotal with multiple items and different discounts

def test_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("small", 2.0, 9)   # no discount
    c.add_item("medium", 3.0, 10) # 5%
    c.add_item("large", 4.0, 50)  # 10%
    total = (2.0*9)+(3.0*10*(1-0.05))+(4.0*50*(1-0.10))
    assert round2(c.subtotal()) == round2(total)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("book", 20.0, 5)   # no bulk discount
    subtotal = 20.0*5
    # apply 10% coupon -> 18.0
    after_coupon = round2(subtotal * (1-0.10))
    shipping = cart.shipping_fee(after_coupon, member=False)
    total_expected = round2(after_coupon + shipping)
    assert c.total(coupon="SAVE10") == total_expected

# total without coupon, with free shipping

def test_total_free_shipping():
    c = cart.Cart()
    c.add_item("expensive", 300.0, 4)  # subtotal 1200 >1000
    assert c.total() == 1200.00

# invalid coupon raises ValueError

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 10.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# empty cart total is zero (no shipping)

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
