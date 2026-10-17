import pytest
import cart

# Helper for rounding comparison
@staticmethod

def approx_equal(a, b, tol=1e-9):
    return abs(a - b) < tol

# Test apply_discount
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0)
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Invalid price or percent
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    ("   SaVe30", 30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVEXX", "DISCOUNT10", "", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 2.5, 3)
    assert empty_cart.items() == {"apple": 3}

def test_add_item_increase(empty_cart):
    empty_cart.add_item("banana", 1.0, 2)
    empty_cart.add_item("banana", 1.0, 3)
    assert empty_cart.items() == {"banana": 5}

# Adding with different unit price raises ValueError
def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("pear", 2.0)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 3.0)

# Invalid quantity or unit_price
@pytest.mark.parametrize("qty,price", [(0,1),(1,-1)])
def test_add_item_invalid(qty, price):
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("item", price, qty)

# remove_item tests
def test_remove_partial(empty_cart):
    empty_cart.add_item("orange", 1.5, 4)
    empty_cart.remove_item("orange", 2)
    assert empty_cart.items() == {"orange": 2}

def test_remove_all(empty_cart):
    empty_cart.add_item("grape", 0.8, 3)
    empty_cart.remove_item("grape", 3)
    assert empty_cart.items() == {}

# Removing non-existent raises KeyError
def test_remove_nonexistent():
    c=cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonitem")

# subtotal and total calculation
@pytest.mark.parametrize("member,coupon", [(False,None),(True,"SAVE10")])
def test_subtotal_total(member, coupon):
    c = cart.Cart()
    c.add_item("tshirt", 50.0, 2)   # subtotal 100
    c.add_item("jeans", 80.0, 1)    # subtotal 180
    assert c.subtotal() == 180.0
    expected_total = 180.0
    if coupon:
        discount_percent=cart.parse_coupon(coupon)
        expected_total -= cart.apply_discount(expected_total, discount_percent)
    if member:
        expected_total += cart.shipping_fee(expected_total, member=True)
    else:
        expected_total += cart.shipping_fee(expected_total, member=False)
    assert c.total(member=member, coupon=coupon) == expected_total
