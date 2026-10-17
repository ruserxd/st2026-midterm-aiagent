import pytest
import cart

# Test apply_discount function
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
    (123.456, 10, 111.11),   # 123.456 * 0.9 = 111.1104 => 111.11
    (50, 33, 33.5),          # 50 * 0.67 = 33.5
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(200, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize("qty, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_percent_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Test parse_coupon
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE15 ", 15),
    ("SaVe50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "foo10",
    "",
    "  ",
    "SAVEABC",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal, member, expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# Test Cart class
def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert not c.items()
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_new_and_existing():
    c = cart.Cart()
    c.add_item("apple", 100, 2)
    assert c.items()["apple"] == 2
    c.add_item("apple", 100, 3)   # increase quantity
    assert c.items()["apple"] == 5

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("banana", 50)
    with pytest.raises(ValueError):
        c.add_item("banana", 60)

@pytest.mark.parametrize("unit_price, quantity", [
    (-10, 1),
    (10, -5),
])
def test_add_item_invalid(unit_price, quantity):
    c = cart.Cart()
    if unit_price < 0:
        with pytest.raises(ValueError):
            c.add_item("orange", unit_price, 1)
    else:
        with pytest.raises(ValueError):
            c.add_item("orange", 10, quantity)

def test_remove_partial():
    c = cart.Cart()
    c.add_item("pear", 20, 3)
    c.remove_item("pear", 1)
    assert c.items()["pear"] == 2

def test_remove_all_and_more():
    c = cart.Cart()
    c.add_item("pear", 20, 2)
    c.remove_item("pear", 2)   # exact removal
    assert "pear" not in c.items()

    c.add_item("pear", 20, 1)
    c.remove_item("pear", 5)   # remove more than existing
    assert "pear" not in c.items()

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("fig")

def test_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("item1", 100, 2)   # 200
    c.add_item("item2", 50, 3)    # 150
    assert c.subtotal() == 350

# Helper for expected total calculation

def _expected_total(subtotal, member=False, coupon_percent=0):
    discounted = round(subtotal * (1 - coupon_percent / 100), 2)
    shipping = cart.shipping_fee(discounted, member)
    return round(discounted + shipping, 2)

def test_cart_total_without_coupon():
    c = cart.Cart()
    c.add_item("widget", 200, 2)   # subtotal 400
    assert c.total() == _expected_total(400)

def test_cart_total_with_member():
    c = cart.Cart()
    c.add_item("widget", 200, 2)
    assert c.total(member=True) == _expected_total(400, member=True)

def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("widget", 200, 2)
    # coupon SAVE10 => percent=10
    assert c.total(coupon="SAVE10") == _expected_total(400, coupon_percent=10)

def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item("widget", 200, 2)
    assert c.total(member=True, coupon="SAVE10") == _expected_total(400, member=True, coupon_percent=10)

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
