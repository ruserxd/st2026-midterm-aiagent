import pytest
import cart

def approx(v, e):
    return round(float(v), 2) == round(float(e), 2)

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert approx(cart.apply_discount(price, percent), result)

@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent (implementation behavior)
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 5),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon (strict uppercase as implemented)
@pytest.mark.parametrize("code,percent", [
    ("SAVE10", 10),
    ("save20", 20),
])
def test_parse_coupon(code, percent):
    if code.islower():
        with pytest.raises(ValueError):
            cart.parse_coupon(code)
    else:
        assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "WRONG", "sAVExx"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member=member) == fee

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart basics
def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# Adding items (no discount case)
def test_add_item_no_discount():
    c = cart.Cart()
    c.add_item("apple", 100, quantity=2)
    assert approx(c.subtotal(), 200.0)
    with pytest.raises(ValueError):
        c.add_item("apple", 120, quantity=1)

# Removing items
def test_remove_item():
    c = cart.Cart()
    c.add_item("item", 200, quantity=5)
    c.remove_item("item", quantity=3)
    assert c.items() == {"item": 2}
    c.remove_item("item", quantity=5)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# Total with coupon (shipping based on subtotal bug)
def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=10)  # 5% discount -> 1900
    assert approx(c.subtotal(), 1900.0)
    total_after_coupon = cart.apply_discount(1900.0, 10)
    shipping_fee_val = cart.shipping_fee(1900.0, member=False)
    expected = round(total_after_coupon + shipping_fee_val, 2)
    assert approx(c.total(coupon="SAVE10"), expected)

# Empty cart total is zero
def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.0
