import pytest
import cart

# ---------- Function tests ----------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full free
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# edge cases: invalid inputs
@pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount percent
@pytest.mark.parametrize("quantity,result", [
    (9, 0),   # below 10
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVEX", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee
@pytest.mark.parametrize("subtotal,member,result", [
    (999.99, False, 60),
    (1000, True, 0),
    (500, True, 30),
    (0, False, 60),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# add_item and quantity increase

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == 3.0   # no bulk discount yet
    c.add_item("apple", 1.00, 7)  # total quantity now 10 -> 5% bulk
    # subtotal: 10 * 1.00 = 10; bulk discount 5% => 9.5
    assert c.subtotal() == 9.5
    c.remove_item("apple", 4)
    # remaining qty 6, no bulk discount
    assert c.items() == {"apple": 6}
    assert c.subtotal() == 6.0
    # remove all
    c.remove_item("apple", 6)
    assert c.items() == {}
    assert c.subtotal() == 0.0

# adding with different unit price raises ValueError

def test_add_different_price():
    c = cart.Cart()
    c.add_item("banana", 0.50, 2)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.60, 1)

# removing non-existent item raises KeyError

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200.0, 5)   # qty=5 -> no bulk discount
    subtotal = 1000.0
    # apply coupon SAVE10 => 10% off
    total_before_shipping = subtotal * 0.9
    shipping = cart.shipping_fee(total_before_shipping)
    expected_total = round(total_before_shipping + shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total

# empty cart should not charge shipping

def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0

# coupon validation inside Cart.total raises ValueError for invalid code

def test_invalid_coupon_in_total():
    c = cart.Cart()
    c.add_item("item", 10.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
