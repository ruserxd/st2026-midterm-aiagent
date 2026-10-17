import cart
import pytest
from decimal import Decimal

round2 = lambda x: round(x, 2)

# ---------- function tests ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),  # spec: 10 for 50
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),  # case‑insensitive
        (" SAVE20 ", 20),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["DISCOUNT10", "SAVE0", "SAVE51", "SAVEXX", ""])  
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1000, True, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.0, quantity=3)
    c.add_item('banana', 1.5)
    assert c.items() == {'apple': 3, 'banana': 1}

def test_cart_add_same_name_diff_price():
    c = cart.Cart()
    c.add_item('item', 5.0)
    with pytest.raises(ValueError):
        c.add_item('item', 6.0)

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item('pear', 1.0, quantity=4)
    c.remove_item('pear', quantity=2)
    assert c.items() == {'pear': 2}
    c.remove_item('pear', quantity=3)  # should remove completely
    assert c.items() == {}

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('ghost')

def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item('unit', 1.0, quantity=10)
    assert c.subtotal() == round2(10 * 1.0 * (1 - 0.05))

def test_cart_subtotal_multiple():
    c = cart.Cart()
    c.add_item('small', 10.0, quantity=5)   # 0% discount
    c.add_item('medium', 20.0, quantity=15) # 5% discount
    small_total = 10 * 5
    medium_total = 20 * 15 * 0.95
    assert c.subtotal() == round2(small_total + medium_total)

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_member_coupon():
    c = cart.Cart()
    c.add_item('expensive', 100.0, quantity=12)  # 5% bulk discount
    subtotal = 100 * 12 * 0.95
    amount_after_coupon = subtotal * 0.90  # SAVE10 -> 10%
    shipping = cart.shipping_fee(subtotal, member=True)
    expected_total = round2(amount_after_coupon + shipping)
    assert c.total(member=True, coupon='SAVE10') == expected_total

# Shipping uses subtotal only

def test_cart_shipping_considers_subtotal_only():
    c = cart.Cart()
    c.add_item('cheap', 5.0, quantity=1)
    # Subtotal before discount = 5
    assert cart.shipping_fee(c.subtotal(), member=False) == 60
    expected_total = round2(4.95 + 60)  # coupon SAVE1 reduces to 4.95 then add shipping
    assert c.total(coupon='SAVE1') == expected_total
