import pytest
import cart

# Helper to round floats for comparison
round2 = lambda x: round(float(x), 2)

@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert round2(cart.apply_discount(price, percent)) == round2(expected)

@pytest.mark.parametrize("price, percent", [
    (-1, 10),
    (10, -5),
    (10, 105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity, expected", [
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

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("SaVe5", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVEX",
    "REDEEM10",
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal, member, expected", [
    (1200, False, 0),
    (1200, True, 0),
    (900, False, 60),
    (900, True, 30),
    (0, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 100.0, quantity=3)
    c.add_item('banana', 50.0)
    items = c.items()
    assert {'name': 'apple', 'unit_price': 100.0, 'quantity': 3} in items
    assert {'name': 'banana', 'unit_price': 50.0, 'quantity': 1} in items


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item('apple', 100.0, quantity=3)
    c.remove_item('apple', quantity=2)
    assert c.items()[0]['quantity'] == 1
    # removing more than present should remove the item entirely
    c.remove_item('apple', quantity=5)
    assert len(c.items()) == 0


def test_cart_subtotal_and_total_no_shipping():
    c = cart.Cart()
    c.add_item('item', 400.0, quantity=3)   # subtotal 1200 -> free shipping
    assert round2(c.subtotal()) == 1200.0
    assert round2(c.total()) == 1200.0


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('item', 500.0, quantity=2)   # subtotal 1000
    # coupon SAVE10 -> 10% off => 900, shipping still free because >=1000 after discount
    assert round2(c.total(coupon='SAVE10')) == 900.0


def test_cart_total_with_member_shipping():
    c = cart.Cart()
    c.add_item('item', 400.0, quantity=3)   # subtotal 1200 -> free shipping
    # member flag has no effect when shipping is free
    assert round2(c.total(member=True)) == 1200.0


def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item('item', 400.0, quantity=3)   # subtotal 1200 -> free shipping
    # coupon reduces amount but still >=1000 after discount, so free shipping
    assert round2(c.total(member=True, coupon='SAVE5')) == 1140.0


def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item('item', 200.0)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
