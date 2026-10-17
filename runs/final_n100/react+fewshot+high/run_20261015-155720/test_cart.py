import pytest
import cart

# Helper for rounding to two decimals as per the specification
r = lambda x: round(float(x), 2)

@pytest.fixture
def empty_cart():
    return cart.Cart()

# ------------------- apply_discount -------------------------------------

@ pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@ pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (10, -5),   # negative percent
    (10, 105),  # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------- bulk_discount_percent ---------------------------------

@ pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------- parse_coupon ----------------------------------------

@ pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),   # case-insensitive
    (" SAVE30 ", 30),  # surrounding whitespace ignored
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@ pytest.mark.parametrize("code", [
    "SAVEXY",   # invalid format
    "SAVE0",     # percent <1
    "SAVE51",    # percent >50
    "SAVE",      # missing number
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------- shipping_fee ----------------------------------------

@ pytest.mark.parametrize("subtotal,member,expected", [
    (999.5, False, 60),
    (999.5, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------- Cart class tests ------------------------------------

@pytest.mark.parametrize("name,unit_price,quantity", [
    ("apple", 1.0, 3),
    ("banana", 0.5, 2),
])
def test_cart_add_item_basic(empty_cart, name, unit_price, quantity):
    empty_cart.add_item(name, unit_price, quantity)
    assert empty_cart.items() == {name: quantity}

@pytest.mark.parametrize("existing_qty,new_qty", [(1, 4), (2, 5)])
def test_cart_add_existing_increases(empty_cart, existing_qty, new_qty):
    name = "item"
    unit_price = 3.0
    empty_cart.add_item(name, unit_price, existing_qty)
    empty_cart.add_item(name, unit_price, new_qty)
    assert empty_cart.items() == {name: existing_qty + new_qty}

def test_cart_add_existing_wrong_price(empty_cart):
    name = "item"
    empty_cart.add_item(name, 1.0, 2)
    with pytest.raises(ValueError):
        empty_cart.add_item(name, 2.0, 3)

@pytest.mark.parametrize("unit_price,quantity", [(-5, 1), (1, 0), (1, -3)])
def test_cart_add_item_errors(empty_cart, unit_price, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("baditem", unit_price, quantity)

def test_cart_remove_item_basic(empty_cart):
    name = "widget"
    unit_price = 5.0
    empty_cart.add_item(name, unit_price, 5)
    empty_cart.remove_item(name, 2)
    assert empty_cart.items() == {name: 3}

def test_cart_remove_all(empty_cart):
    name = "thing"
    empty_cart.add_item(name, 10.0, 2)
    empty_cart.remove_item(name, 2)  # should remove entirely
    assert empty_cart.items() == {}

def test_cart_remove_more_than_exists(empty_cart):
    name = "excess"
    empty_cart.add_item(name, 4.0, 1)
    empty_cart.remove_item(name, 5)
    assert empty_cart.items() == {}

def test_cart_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("ghost", 1)

def test_cart_subtotal_basic(empty_cart):
    # two items: A at 2.0*3=6, B at 5.5*1=5.5
    empty_cart.add_item("A", 2.0, 3)
    empty_cart.add_item("B", 5.5, 1)
    assert empty_cart.subtotal() == 11.5

def test_cart_total_no_coupon_nonmember(empty_cart):
    empty_cart.add_item("A", 10.0, 2)   # subtotal 20
    expected = r(20 + cart.shipping_fee(20))
    assert empty_cart.total() == expected

def test_cart_total_with_coupon(empty_cart):
    empty_cart.add_item("C", 40.0, 1)
    discounted = 40.0 * (1 - cart.parse_coupon("SAVE10") / 100)
    expected = r(discounted + cart.shipping_fee(discounted))
    assert empty_cart.total(coupon="SAVE10") == expected

def test_cart_total_member_with_coupon(empty_cart):
    # subtotal before coupon 1100, after 20% discount -> 880 (<1000)
    empty_cart.add_item("D", 1100.0, 1)
    discounted = 1100.0 * (1 - cart.parse_coupon("SAVE20") / 100)
    expected = r(discounted + cart.shipping_fee(discounted, member=True))
    assert empty_cart.total(member=True, coupon="SAVE20") == expected

@pytest.mark.parametrize("coupon", ["BADCODE", "SAVE101"])
def test_cart_total_invalid_coupon(empty_cart, coupon):
    with pytest.raises(ValueError):
        empty_cart.total(coupon=coupon)

def test_cart_total_empty(empty_cart):
    assert empty_cart.total() == 0

def test_cart_total_rounding(empty_cart):
    # price 10.555 leads to subtotal 10.555, shipping 60
    empty_cart.add_item("E", 10.555, 1)
    expected = r(10.555 + cart.shipping_fee(10.555))
    assert empty_cart.total() == expected
