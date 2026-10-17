import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (-1, 10),      # negative price
    (100, -5),     # negative percent
    (100, 105),    # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_breakpoints():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon('SAVE10') == 10
    assert parse_coupon('save20') == 20
    assert parse_coupon(' SAVE30 ') == 30

@pytest.mark.parametrize("code", [
    'SAVEX',          # non-numeric
    'SAVEN0',         # out of range 1-50
    'SAVEN51',        # out of range
    'DISCOUNT10',     # wrong prefix
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(200, member=False) == 60

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart.total ----------

def test_cart_total_empty():
    cart = Cart()
    assert cart.total() == 0


def test_cart_total_with_items_no_coupon_member():
    cart = Cart()
    cart.add_item('apple', 200, quantity=3)   # subtotal 600
    assert cart.subtotal() == 600
    # no coupon -> shipping fee 60, total 660
    assert cart.total() == 660


def test_cart_total_with_coupon_and_member():
    cart = Cart()
    cart.add_item('banana', 300, quantity=4)   # subtotal 1200 >=1000 free shipping
    # apply coupon SAVE10 -> discount 10% of 1200 => 1080
    total = cart.total(member=True, coupon='SAVE10')
    assert total == 1080


def test_cart_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item('orange', 100)
    with pytest.raises(ValueError):
        cart.total(coupon='BADCODE')

# ---------- ensure rounding to two decimals ----------

def test_rounding_behavior():
    # subtotal: 333, coupon SAVE10 -> 299.7 -> round to 299.70
    cart = Cart()
    cart.add_item('item', 333)
    assert cart.total(coupon='SAVE10') == 359.7   # 333*0.9 + 60 shipping
    # test with a value that would require rounding: e.g., subtotal 115.555
    cart = Cart()
    cart.add_item('thing', 115.555)
    assert round(cart.total(), 2) == round(115.555 + 60, 2)
