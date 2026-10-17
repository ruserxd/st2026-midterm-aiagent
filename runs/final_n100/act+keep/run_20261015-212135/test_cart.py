import pytest
import cart
from decimal import Decimal

round2 = lambda x: round(Decimal(str(x)), 2)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("q", [0, -5, 3.2])
def test_bulk_discount_invalid(q):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(q)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["",
                                   "SAVE0",
                                   "SAVENONE",
                                   "DISCOUNT10",
                                   " SAVE51 ",
                                   123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (50.5, True, 30),
    (1000, False, 0),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-10, -5.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart fixture
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item and subtotal
def test_add_and_subtotal(empty_cart):
    c = empty_cart
    c.add_item("apple", 20.0, quantity=5)
    assert round2(c.subtotal()) == round2(5 * 20.0)
    c.add_item("apple", 20.0, quantity=3)
    assert c.items() == [({"name": "apple", "unit_price": 20.0, "quantity": 8})]
    assert round2(c.subtotal()) == round2(8 * 20.0)
    c.add_item("banana", 10.0, quantity=12)
    expected_sub = 8*20 + 12*10*(1-0.05)
    assert round2(c.subtotal()) == round2(expected_sub)

# price mismatch
def test_add_item_price_mismatch(empty_cart):
    c = empty_cart
    c.add_item("orange", 15.0, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("orange", 20.0, quantity=1)

# invalid qty
@pytest.mark.parametrize("qty", [0, -3, 1.5])
def test_add_item_invalid_qty(empty_cart, qty):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 5.0, quantity=qty)

def test_add_negative_price():
    with pytest.raises(ValueError):
        cart.Cart().add_item("negprice", -1.0, quantity=1)

# remove_item tests
def test_remove_item(empty_cart):
    c = empty_cart
    c.add_item("mango", 10.0, quantity=4)
    c.remove_item("mango", quantity=2)
    assert c.items() == [({"name": "mango", "unit_price": 10.0, "quantity": 2})]
    c.remove_item("mango", quantity=2)
    assert c.items() == []

def test_remove_nonexistent():
    with pytest.raises(KeyError):
        cart.Cart().remove_item("ghost")

# Cart.total tests
@pytest.fixture
def cart_with_items():
    c = cart.Cart()
    c.add_item("itemA", 200.0, quantity=3)
    c.add_item("itemB", 100.0, quantity=6)
    return c

def test_subtotal_cart(cart_with_items):
    assert round2(cart_with_items.subtotal()) == round2(600 + 540)

def test_total_no_coupon_member(cart_with_items):
    assert cart_with_items.total(member=True) == round2(1140.00)

def test_total_coupon_no_member(cart_with_items):
    total = cart_with_items.total(coupon="SAVE10")
    expected = round2(1140 * 0.90)
    assert total == expected

def test_total_coupon_member(cart_with_items):
    total = cart_with_items.total(member=True, coupon="SAVE20")
    expected = round2(1140 * 0.80)
    assert total == expected

def test_total_invalid_coupon():
    with pytest.raises(ValueError):
        cart.Cart().total(coupon="BADCODE")

def test_empty_cart_total():
    assert cart.Cart().total() == 0
