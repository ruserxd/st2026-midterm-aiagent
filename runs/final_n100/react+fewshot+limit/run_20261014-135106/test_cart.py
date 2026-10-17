import pytest
import cart

# Utility tests for standalone functions
@pytest.mark.parametrize("quantity,expected", [
    (5,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("price,percent,expected", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0)
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    (" save20 ",20),
    ("SaVe5",5)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVEXY",
    "10SAVE",
    "",
    "   ",
    123,
    None
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected", [
    (0,False,60),
    (500,True,30),
    (1000,False,0),
    (1500,True,0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Tests for Cart class
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_and_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 2)
    c.add_item("banana", 0.75, 3)
    assert c.items() == {"apple": (1.5, 2), "banana": (0.75, 3)}

def test_add_same_increases_quantity(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 1)
    c.add_item("apple", 1.0, 4)
    assert c.items() == {"apple": (1.0, 5)}

def test_add_price_mismatch(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)

def test_invalid_unit_price_and_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", -1, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 1, 0)

def test_remove_item(empty_cart):
    c = empty_cart
    c.add_item("pear", 2.0, 3)
    c.remove_item("pear", 1)
    assert c.items() == {"pear": (2.0, 2)}
    c.remove_item("pear", 2)
    assert "pear" not in c.items()

def test_remove_more_than_present(empty_cart):
    c = empty_cart
    c.add_item("pear", 2.0, 1)
    c.remove_item("pear", 5)
    assert "pear" not in c.items()

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("kiwi", 1)

def test_subtotal_and_total():
    c = cart.Cart()
    c.add_item("milk", 3.0, 2)   # $6
    c.add_item("bread", 2.5, 4)  # $10
    assert c.subtotal() == 16.0
    expected_total = 16.0 + cart.shipping_fee(16.0)
    assert c.total() == expected_total

    # add bulk discounted item
    c.add_item("chocolate", 1.0, 12)  # $12
    assert c.subtotal() == 28.0
    # shipping for subtotal 28
    shipping = cart.shipping_fee(28.0)
    # apply coupon
    total_with_coupon = c.total(coupon="SAVE10")
    assert total_with_coupon == (28.0 + shipping) * 0.9
    # member discount: shipping half
    assert c.total(member=True) == (28.0 + shipping/2)

# Test that invalid coupon type raises ValueError
def test_total_invalid_coupon_type(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon=123)
