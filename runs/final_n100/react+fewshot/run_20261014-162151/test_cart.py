import pytest
import cart

# Helper to create a cart with items
def make_cart(items=None):
    c = cart.Cart()
    if items:
        for name, price, qty in items:
            c.add_item(name, price, qty)
    return c

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 110])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,expected", [
    (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
valid_codes = ["SAVE10", "save20", " Save30 "]
@pytest.mark.parametrize("code", valid_codes)
def test_parse_coupon_valid(code):
    # Expected percent extracted case-insensitively after stripping whitespace
    expected = int(code.strip().upper()[4:])
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVE51", "SAVEXX", "12345", ""]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0)
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart add_item / remove_item behavior ----------
def test_cart_add_remove_behavior():
    c = make_cart()
    c.add_item('apple', 2.0, 3)
    assert c.items() == {'apple': 3}
    # Adding same item increases quantity; price must match
    c.add_item('apple', 2.0, 2)
    assert c.items() == {'apple': 5}
    with pytest.raises(ValueError):
        c.add_item('apple', 1.99, 1)  # price mismatch
    with pytest.raises(ValueError):
        c.add_item('banana', -1.0, 1)
    with pytest.raises(ValueError):
        c.add_item('banana', 1.0, 0)
    # remove item
    c.remove_item('apple', 3)
    assert c.items() == {'apple': 2}
    c.remove_item('apple', 2)  # should remove completely
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item('orange', 1)

# ---------- subtotal calculations with bulk discounts ----------
def test_subtotal_with_bulk_discounts():
    c = make_cart([('item1', 10.0, 5), ('item2', 20.0, 50)])
    # item1: qty 5 -> no discount => 10*5=50
    # item2: qty 50 -> bulk_discount_percent = 10% => unit price after discount = 18
    expected_item2_total = 18.0 * 50
    expected_subtotal = round(50 + expected_item2_total, 2)
    assert c.subtotal() == expected_subtotal

# ---------- total with coupon and shipping ----------
def test_total_with_coupon_and_shipping():
    c = make_cart([('widget', 100.0, 20)])
    # widget qty 20 -> bulk discount 5% => unit price 95
    subtotal_widget = 95.0 * 20
    amount_after_coupon = cart.apply_discount(subtotal_widget, cart.parse_coupon('SAVE10'))
    total_expected = round(amount_after_coupon + cart.shipping_fee(amount_after_coupon), 2)
    assert c.total(coupon='SAVE10') == total_expected

# Member discount on shipping only affects shipping fee calculation

def test_total_member_shipping_discount():
    c_member = make_cart([('gadget', 50.0, 3)])
    # gadget qty 3 no bulk => subtotal 150
    amount_after_coupon = cart.apply_discount(150, cart.parse_coupon('SAVE10')) if False else 150
    # no coupon in test; use total directly
    total_expected = round(150 + cart.shipping_fee(150, member=True), 2)
    assert c_member.total(member=True) == total_expected

# Empty cart total is 0 (no shipping charged)
def test_empty_cart_total():
    empty_cart = cart.Cart()
    assert empty_cart.total() == 0
