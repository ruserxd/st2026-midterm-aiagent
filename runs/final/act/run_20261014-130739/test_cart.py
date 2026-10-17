import pytest
import cart

# Utility for rounding

def round2(x):
    return round(x, 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50.75, 10, 45.675),
])
def test_apply_discount_success(price, percent, expected):
    assert cart.apply_discount(price, percent) == round2(expected)

@pytest.mark.parametrize("price,percent", [(-1, 20), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (99, 10), (50, 10), (49, 5), (10, 5), (9, 0),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [-1, 0, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10), ("save20 ", 20), ("   SaVe5", 5),
])
def test_parse_coupon_success(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEE10", "SAVE0", "save51", "abc", " "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0), (1000, True, 0), (999.99, False, 60), (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class basic tests ----------

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}

def test_cart_operations_and_totals():
    c = cart.Cart()
    c.add_item("apple", 100, quantity=3)
    c.add_item("banana", 50)
    # subtotal should be 300 + 50 = 350
    assert c.subtotal() == 350
    # remove one apple -> 250
    c.remove_item("apple")
    assert c.subtotal() == 250
    # total should not raise and be >= subtotal
    tot = c.total(member=False, coupon=None)
    assert tot >= c.subtotal()
    # member discount via coupon if provided
    if hasattr(cart, 'parse_coupon'):
        tot_coup = c.total(member=True, coupon="SAVE10")
        assert tot_coup >= c.subtotal()
