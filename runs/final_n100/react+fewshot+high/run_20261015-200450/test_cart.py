import pytest
import cart

# 1. apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (1.23, 10, 1.11),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

def test_apply_discount_invalid():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)

# 2. bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # spec expects 10; bug will return 5
    (51, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.7])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# 3. parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),          # should be case‑insensitive; bug will fail
    (" SAVE20 ", 20)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [None, "SAVEx", "SAVE0", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# 4. shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (999, False, 60),
    (500, True, 30),
    (1200, False, 0),     # free for >=1000
    (1200, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# 5. Cart tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_and_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 5}

def test_add_item_invalid_unit_price(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", -1, 1)

def test_add_item_invalid_quantity(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 0.5, 0)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 0.5, -2)
    with pytest.raises(ValueError):
        empty_cart.add_item("peach", 0.5, 1.5)

def test_add_item_different_price(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)

def test_remove_item_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 5)
    # remove part of quantity
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}
    # remove remaining quantity exactly
    c.remove_item("apple", 3)
    # spec expects item removed entirely -> empty dict
    assert c.items() == {}
    # add another item for further tests
    c.add_item("orange", 0.5, 1)
    with pytest.raises(KeyError):
        c.remove_item("banana", 1)

def test_subtotal():
    c = cart.Cart()
    c.add_item("item1", 100, 10)   # bulk_discount_percent(10)=5%
    c.add_item("item2", 200, 50)   # bulk_discount_percent(50)=10% (spec)
    expected = round(100*10*(1-0.05) + 200*50*(1-0.10), 2)
    assert c.subtotal() == expected

def test_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0.0

def test_total_no_coupon_member_false():
    c = cart.Cart()
    c.add_item("big", 200, 5)   # subtotal 1000
    assert c.total() == 1000.0

def test_total_with_coupon_below_threshold():
    c = cart.Cart()
    c.add_item("item", 300, 4)  # subtotal 1200
    # coupon 20% reduces to 960; shipping fee 60 for non‑member -> total expected 1020
    assert c.total(coupon="SAVE20") == 1020.0

def test_total_with_coupon_below_threshold_member():
    c = cart.Cart()
    c.add_item("item", 300, 4)  # subtotal 1200
    assert c.total(member=True, coupon="SAVE20") == 990.0

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
