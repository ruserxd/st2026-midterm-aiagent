import pytest
import cart

# Helper for creating a cart with items

def make_cart(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    # edge cases
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon(' save5 ') == 5
    assert cart.parse_coupon('sAvE50') == 50

@ pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart subtotal ----------

def test_cart_subtotal_no_discount():
    c = make_cart([('apple', 2.0, 1), ('banana', 1.5, 3)])
    assert c.subtotal() == round(2.0*1 + 1.5*3, 2)

def test_cart_subtotal_with_bulk_discount():
    # 10 units => 5% discount
    c = make_cart([('widget', 100.0, 10)])
    expected = cart.apply_discount(100.0 * 10, cart.bulk_discount_percent(10))
    assert c.subtotal() == round(expected, 2)

# ---------- Cart total with shipping and coupon ----------

def test_cart_total_no_items():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_member_coupon():
    # subtotal after bulk discount
    c = make_cart([('item', 200.0, 10)])  # 5% discount on 10 units => 1900
    # apply coupon 10%
    amount_after_discount = cart.apply_discount(1900, 10)  # 1710
    # shipping for member on discounted amount -> half of 60 = 30 (since subtotal <1000)
    expected_total = round(amount_after_discount + 30, 2)
    assert c.total(member=True, coupon='SAVE10') == expected_total

# ---------- Cart remove_item logic ----------

def test_remove_more_than_exists():
    c = make_cart([('item', 50.0, 3)])
    # remove 5 units; item should be removed entirely
    c.remove_item('item', 5)
    assert 'item' not in c.items()

# ---------- Add item with mismatched unit price ----------

def test_add_item_price_mismatch():
    c = make_cart([('item', 20.0, 2)])
    with pytest.raises(ValueError):
        c.add_item('item', 25.0)

# ---------- remove non-existent item ----------

def test_remove_nonexistent_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('ghost')
