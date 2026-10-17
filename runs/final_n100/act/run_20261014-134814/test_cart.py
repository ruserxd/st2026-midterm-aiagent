import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- discount functions ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [ -1, -5.6 ])
@ pytest.mark.parametrize("percent", [ 10, 20 ])
def test_apply_discount_negative_price(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@ pytest.mark.parametrize("percent", [ -0.1, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk discount ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("q", [0, -1, 3.5])
def test_bulk_discount_invalid(q):
    with pytest.raises(ValueError):
        bulk_discount_percent(q)

# ---------- coupon parsing ----------

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save50') == 50
    assert parse_coupon(' SAVE25 ') == 25
    # case-insensitive and whitespace stripping
    assert parse_coupon('\tSaVe5\n') == 5

@ pytest.mark.parametrize("code", [
    'SAV10',       # missing S
    'SAVE0',       # below min
    'SAVE51',      # above max
    'SAVE-1',      # negative number
    'saveabc',     # non-numeric
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    # members pay half
    assert shipping_fee(50, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item('apple', 1.0, 3)
    assert c.items() == {'apple': 3}
    # add same item increases quantity
    c.add_item('apple', 1.0, 2)
    assert c.items() == {'apple': 5}
    # adding different item
    c.add_item('banana', 0.5, 10)
    assert c.items() == {'apple': 5, 'banana': 10}

@ pytest.mark.parametrize("name", ['orange', 'pear'])
def test_remove_nonexistent(name):
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item(name)

def test_remove_item_and_zero_quantity():
    c = Cart()
    c.add_item('x', 2.0, 4)
    c.remove_item('x', 2)
    assert c.items() == {'x': 2}
    # removing remaining quantity removes item
    c.remove_item('x', 2)
    assert 'x' not in c.items()

# ----- subtotal calculations with bulk discount -----

def test_subtotal_no_discount():
    c = Cart()
    c.add_item('item', 10, 3)  # below bulk threshold
    assert c.subtotal() == 30.0

def test_subtotal_with_bulk_discount():
    c = Cart()
    # quantity 12 -> 5% discount on that item
    c.add_item('bulk', 100, 12)
    expected = apply_discount(1200, 5)  # 5% off 1200
    assert c.subtotal() == round(expected, 2)

# ----- total calculation -----

def test_total_empty_cart():
    c = Cart()
    assert c.total() == 0.0

def test_total_without_coupon_and_member_false():
    c = Cart()
    c.add_item('a', 100, 2)  # subtotal 200, no bulk discount
    expected_subtotal = 200.0
    # no coupon -> amount = 200
    shipping = shipping_fee(200)
    assert c.total() == round(expected_subtotal + shipping, 2)

def test_total_with_coupon_and_member():
    c = Cart()
    c.add_item('a', 50, 20)  # quantity 20 -> 10% bulk discount
    subtotal_before_coupon = apply_discount(1000, 10)  # 1000*0.9=900
    # coupon SAVE5 -> 5%
    after_coupon = apply_discount(subtotal_before_coupon, 5)
    shipping = shipping_fee(after_coupon, member=True)
    total_expected = round(after_coupon + shipping, 2)
    assert c.total(member=True, coupon='SAVE5') == total_expected

# ----- validate errors on invalid data for Cart methods -----

def test_add_item_invalid_price_or_quantity():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item('bad', -1, 1)
    with pytest.raises(ValueError):
        c.add_item('bad', 5, 0)

def test_add_item_conflicting_price():
    c = Cart()
    c.add_item('conflict', 10, 2)
    with pytest.raises(ValueError):
        c.add_item('conflict', 12, 1)
