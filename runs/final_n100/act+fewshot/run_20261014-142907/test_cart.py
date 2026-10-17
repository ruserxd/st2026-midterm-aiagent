import pytest
import cart

# Helper for float comparison
@pytest.fixture(autouse=True)
def enable_float_close():
    pass

# Test apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),          # negative price
    (100, -5),         # negative percent
    (100, 105),        # percent > 100
])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize("qty,percent", [
    (9, 0),   # below 10
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0, -5, 1.5])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Test parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30  ", 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAV10",            # missing 'E'
    "SAVE0",            # N < 1
    "SAVE51",           # N > 50
    "SAVE-5",           # negative number
    "saveabc",          # non numeric
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-10, -1e-3])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Test Cart functionality
class DummyCart(cart.Cart):
    # Inherit to expose internal state if needed
    pass

@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_cart_total(empty_cart):
    assert empty_cart.total() == 0

# Adding items and subtotal
@pytest.mark.parametrize("items,expected_subtotal", [
    ([('apple', 1.00, 3)], 3.00),          # single item multiple quantity
    ([('banana', 0.5), ('orange', 0.75, 2)], 1.75),
])
def test_cart_subtotal(items, expected_subtotal):
    c = cart.Cart()
    for name, price, *rest in items:
        qty = rest[0] if rest else 1
        c.add_item(name, price, qty)
    assert c.subtotal() == pytest.approx(expected_subtotal, rel=1e-9)

# Total with coupon and shipping
@pytest.mark.parametrize("items,coupon,total", [
    ([('item', 200)], None, 260.0),   # 200 + 60 shipping
    ([('item', 200)], 'SAVE10', 230.0), # 180 + 50 shipping? 180<1000 so 60
    ([('item', 1100)], None, 1100.0), # free shipping
])
def test_cart_total(items, coupon, total):
    c = cart.Cart()
    for name, price, *rest in items:
        qty = rest[0] if rest else 1
        c.add_item(name, price, qty)
    assert c.total(coupon=coupon) == pytest.approx(total, rel=1e-9)

# Member discount applied to shipping only
@pytest.mark.parametrize("items,total", [
    ([('item', 200)], 260.0),
])
def test_cart_total_member(items, total):
    c = cart.Cart()
    for name, price, *rest in items:
        qty = rest[0] if rest else 1
        c.add_item(name, price, qty)
    # member flag should affect shipping
    assert c.total(member=True) == pytest.approx(total - 30.0 + 60.0, rel=1e-9)

# Removing items

def test_remove_item():
    c = cart.Cart()
    c.add_item('x', 5.0, 3)
    c.remove_item('x')  # default qty 1 -> remaining 2
    assert len(c.items()) == 1 and c.items()[0]['quantity'] == 2
    c.remove_item('x', 2)  # remove all
    assert not c.items()

# Removing more than existing raises ValueError

def test_remove_more_than_exists():
    c = cart.Cart()
    c.add_item('y', 1.0, 2)
    with pytest.raises(ValueError):
        c.remove_item('y', 3)
