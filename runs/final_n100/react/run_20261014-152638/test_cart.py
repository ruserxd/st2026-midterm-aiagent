import pytest
import cart

# Helper for creating a cart with items

def make_cart(**items):
    c = cart.Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    return c

# ---------- apply_discount -------------------------------------------------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
        (123.456, 20, round(123.456*80/100,2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------

@pytest.mark.parametrize(
    "qty,expected",
    [
        (5, 0),
        (10, 5),
        (51, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ---------------------------------------------------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SAVE30  ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "XYZ", 123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

# Assume thresholds from spec: FREE_SHIPPING_THRESHOLD=1000, SHIPPING_BASE=60
FREE = getattr(cart, 'FREE_SHIPPING_THRESHOLD', 1000)
BASE = getattr(cart, 'SHIPPING_BASE', 60)

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, BASE),
        (999.99, True, BASE/2),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality --------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 100, 2)
    assert c.items() == {'apple': 2}
    c.add_item('apple', 100, 3)
    assert c.items() == {'apple': 5}

    with pytest.raises(ValueError):
        c.add_item('apple', 90, 1)  # price mismatch

def test_cart_remove():
    c = cart.Cart()
    c.add_item('banana', 50, 4)
    c.remove_item('banana', 2)
    assert c.items() == {'banana': 2}
    c.remove_item('banana', 2)
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

# Subtotal with bulk discount

def test_subtotal_bulk_discount():
    c = cart.Cart()
    # 10 units at $10 each => 100, should get 5% off -> 95.0
    c.add_item('widget', 10, 10)
    assert c.subtotal() == pytest.approx(95.0)
    # 51 units of 1 price 2 => line total 102, 10% off -> 91.8
    c.add_item('gadget', 2, 51)
    assert c.subtotal() == pytest.approx(186.8)  # 95+91.8

# Total with coupon and shipping

def test_total_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('item', 2000, 1)  # subtotal 2000 -> free shipping
    assert c.total(coupon='SAVE10') == pytest.approx(1800.0)  # 10% off only
    c2 = cart.Cart()
    c2.add_item('small', 50, 5)
    # subtotal 250, coupon 20% -> 200, shipping 60 (non-member)
    assert c2.total(coupon='SAVE20') == pytest.approx(260.0)  # 200+60
    # member gets half shipping
    assert c2.total(member=True, coupon='SAVE20') == pytest.approx(230.0)

# Empty cart

def test_empty_cart_total_and_shipping():
    c = cart.Cart()
    assert c.total() == 0
    with pytest.raises(ValueError):
        # shipping_fee on empty subtotal should be zero but called in total?
        cart.shipping_fee(0)
