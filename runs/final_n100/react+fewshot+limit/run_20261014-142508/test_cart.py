import pytest
import cart

# helper to create cart and add items quickly
def make_cart(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("code,expected", [
    ('SAVE10', 10),
    ('save20', 20),
    (' SAVE30 ', 30),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0),
    (800, False, 60),
    (800, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Cart behavior tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 1.0, 2)
    c.add_item('banana', 0.5, 4)
    assert c.items() == {'apple': 2, 'banana': 4}

def test_cart_add_existing_increases_quantity_and_price_match():
    c = cart.Cart()
    c.add_item('widget', 10.0, 1)
    c.add_item('widget', 10.0, 3)
    assert c.items() == {'widget': 4}

def test_cart_add_existing_mismatched_price_raises():
    c = cart.Cart()
    c.add_item('gadget', 5.0, 1)
    with pytest.raises(ValueError):
        c.add_item('gadget', 6.0, 2)

@pytest.mark.parametrize("name,quantity", [
    ('apple', 1),
    ('banana', 3),
])
def test_cart_remove_and_auto_remove(name, quantity):
    c = cart.Cart()
    c.add_item('apple', 1.0, 2)
    c.add_item('banana', 0.5, 4)
    # Remove partial
    c.remove_item(name, 1 if name=='apple' else 3)
    expected_qty = {'apple':1,'banana':1}[name]
    assert c.items()[name] == expected_qty


def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent', 1)

# subtotal tests

def test_subtotal_basic_and_bulk_discount():
    c = cart.Cart()
    # 10 apples at $2 each -> bulk discount 5%
    c.add_item('apple', 2.0, 10)
    expected_line = 20.0 * 0.95
    assert c.subtotal() == round(expected_line, 2)


def test_subtotal_multiple_items_with_discounts():
    c = cart.Cart()
    # 5 oranges at $3 -> no bulk discount
    c.add_item('orange', 3.0, 5)
    # 20 pears at $1 -> bulk discount 10%
    c.add_item('pear', 1.0, 20)
    subtotal = 15.0 + 20.0 * 0.9
    assert c.subtotal() == round(subtotal, 2)

# total tests with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # $200 worth before discount; bulk discount 10% -> $180 subtotal
    c.add_item('item', 20.0, 10)
    amount_after_discount = 180 * 0.9  # coupon SAVE10
    shipping = 60  # member False
    total_expected = round(amount_after_discount + shipping, 2)
    assert c.total(member=False, coupon='SAVE10') == total_expected


def test_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0

# Edge cases for apply_discount invalid inputs
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)
