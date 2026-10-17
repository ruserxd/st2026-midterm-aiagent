import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent",[(100,0),(50,100)]
)
def test_apply_discount_edge_bounds(price, percent):
    result = apply_discount(price, percent)
    expected = round(price * (1 - percent/100), 2)
    assert result == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10,20),(50,-5),(30,120)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_bounds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity",[-1,0])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("   SaVe30  ") == 30

@pytest.mark.parametrize("code",["SAVExx","SAVE51","SAVE0","NOTVALID","1234","S AVE10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_free_and_half():
    assert shipping_fee(1200) == 0
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal",[-10,-1])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_items():
    c = Cart()
    c.add_item('apple', 100, quantity=3)
    c.add_item('banana', 150)  # default quantity 1
    assert c.items() == {
        'apple': (100, 3),
        'banana': (150, 1)
    }

def test_cart_remove_and_subtotal():
    c = Cart()
    c.add_item('item', 200, quantity=5)
    c.remove_item('item', quantity=2)
    assert c.items() == {'item': (200, 3)}
    # removing more than existing should remove all
    c.remove_item('item', quantity=10)
    assert 'item' not in c.items()
    assert c.subtotal() == 0

def test_cart_total_empty():
    c = Cart()
    assert c.total() == 0

def test_cart_total_without_coupon_member_and_shipping_free_expected_behavior():
    c = Cart()
    c.add_item('premium', 200, quantity=6)  # 1200 total
    assert c.total() == 1200

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item('premium', 200, quantity=6)
    total = c.total(coupon='SAVE10')
    assert pytest.approx(total) == 1080.0

# Additional test for member discount on shipping.

def test_cart_total_member_shipping_half_expected():
    c = Cart()
    c.add_item('item', 50, quantity=10)  # subtotal 500
    total = c.total(member=True)
    assert pytest.approx(total) == 530.0

# Test that invalid coupon in total raises ValueError

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item('item', 100, quantity=2)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')
