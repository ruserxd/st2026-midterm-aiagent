import pytest
import cart

# Helper for floating comparison

def approx(a, b, rel_tol=1e-9):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), 1e-9)

# apply_discount tests

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests (per spec: positive integer else error; zero invalid)

def test_bulk_discount_zero_quantity_error():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)

@pytest.mark.parametrize("q", [9])
def test_bulk_discount_5percent(q):
    assert cart.bulk_discount_percent(q) == 0

@pytest.mark.parametrize("q", [10, 49])
def test_bulk_discount_5percent_valid(q):
    assert cart.bulk_discount_percent(q) == 5

@pytest.mark.parametrize("q", [50, 150])
def test_bulk_discount_10percent(q):
    assert cart.bulk_discount_percent(q) == 10

@pytest.mark.parametrize("q", [100, 200])
def test_bulk_discount_15percent(q):
    assert cart.bulk_discount_percent(q) == 15

@pytest.mark.parametrize("quantity", [-1, -5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests (case-insensitive, strip whitespace)

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("SaVe5") == 5

@pytest.mark.parametrize("code", ["SAVEX", "123", "", "save0", "save51", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests

def test_shipping_free_for_large_subtotal():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200.5) == 0

@pytest.mark.parametrize("subtotal,expected", [(0, 60), (500, 60)])
def test_shipping_regular(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# member half shipping

def test_shipping_member_half():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(200, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 100)
    assert c.items() == {'apple':1}
    c.add_item('apple', 100, quantity=2)
    assert c.items() == {'apple':3}


def test_cart_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item('banana', 50)
    with pytest.raises(ValueError):
        c.add_item('banana', 60, quantity=1)

@pytest.mark.parametrize("quantity", [-1, 0])
def test_cart_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('cherry', 30, quantity=quantity)

# Removing items

def test_remove_single_and_last():
    c = cart.Cart()
    c.add_item('pear', 70, quantity=3)
    c.remove_item('pear')
    assert c.items() == {'pear':2}
    c.remove_item('pear', quantity=2)
    assert 'pear' not in c.items()

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('orange')

# Subtotal tests

def test_subtotal_simple():
    c = cart.Cart()
    c.add_item('item', 10, quantity=5)
    assert c.subtotal() == 50.0


def test_subtotal_bulk_discount_5percent():
    c = cart.Cart()
    c.add_item('item', 20, quantity=12)
    line_total = 20*12
    discounted = cart.apply_discount(line_total, 5)
    assert approx(c.subtotal(), discounted)

# Total with coupon and shipping per spec

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('item', 200, quantity=2)
    amount_after_coupon = cart.apply_discount(400, 10)
    shipping = cart.shipping_fee(amount_after_coupon, member=False)
    expected_total = round(amount_after_coupon + shipping, 2)
    assert approx(c.total(coupon='SAVE10'), expected_total)

# Member half shipping

def test_member_shipping_half():
    c = cart.Cart()
    c.add_item('item', 200, quantity=1)
    amount_after_coupon = cart.apply_discount(200, 0)
    shipping = cart.shipping_fee(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + shipping, 2)
    assert approx(c.total(member=True), expected_total)

# Empty cart returns zero

def test_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0
    assert c.subtotal() == 0
    assert c.items() == {}
