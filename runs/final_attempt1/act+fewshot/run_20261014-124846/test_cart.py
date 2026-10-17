import pytest
import cart

# Helper to create a cart with known items
def make_cart(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# ---- Tests for utility functions ----

@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.00),
    (100.0, 0, 100.00),
    (50.0, 100, 0.00),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid cases for apply_discount
@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

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

@pytest.mark.parametrize("code", ["SAVE10", "save20", "  SaVe30 "])
def test_parse_coupon_valid(code):
    # discount percent equals the number after SAVE
    number = int(''.join(filter(str.isdigit, code)))
    assert cart.parse_coupon(code) == number

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVExx", "FOO10", "SAVE51", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# ---- Tests for Cart class ----

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.00
    assert c.total() == 0.00

def test_add_item_increases_quantity_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.50, 2)
    assert c.items() == {"apple": 2}
    assert c.subtotal() == 3.00
    # Add same item with same price
    c.add_item("apple", 1.50, 3)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == 7.50

def test_add_item_invalid_price_or_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 1, 0)

def test_add_item_different_price_error():
    c = cart.Cart()
    c.add_item("orange", 2.00, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.00, 1)

def test_remove_item_reduces_quantity_and_removes_when_zero():
    c = cart.Cart()
    c.add_item("pear", 0.80, 4)
    c.remove_item("pear", 2)
    assert c.items() == {"pear": 2}
    assert c.subtotal() == 1.60
    # remove remaining units
    c.remove_item("pear", 2)
    assert c.items() == {}
    assert c.subtotal() == 0.00

def test_remove_nonexistent_item_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("plum", 1)

# total with member discount and coupon
@pytest.mark.parametrize("items,member,coupon,total_expected", [
    ([("item", 100.0, 2)], False, None, 200.00),
    ([("item", 100.0, 2)], True, None, 190.00), # 5% bulk discount because quantity=2? actually <10 no bulk
    ([("item", 100.0, 12)], False, None, 200.00 - 5*2.00),
    ([("item", 500.0, 1)], True, "SAVE20", 500.0 * 0.80 + 30), # member half shipping
])
def test_total(items, member, coupon, total_expected):
    c = make_cart([(name, price, qty) for name, price, qty in items])
    total = c.total(member=member, coupon=coupon)
    assert pytest.approx(total, rel=1e-9) == total_expected
