import pytest
import cart

# Helper to set up a Cart with items

def make_cart_with_items(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# ---------- test apply_discount ---------
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases: rounding to two decimals
@pytest.mark.parametrize("price,percent,result", [
    (99.99, 10, 89.99),  # 99.99 * 0.9 = 89.991 => rounded 89.99
])
def test_apply_discount_rounding(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Validation errors for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-1, 10),  # negative price
    (100, -5),  # negative percent
    (100, 105),  # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- test bulk_discount_percent ---------
@pytest.mark.parametrize("quantity,result", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

# Validation error for negative quantity
with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)

# ---------- test parse_coupon ---------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("SaVe50", 50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# Invalid coupons raise ValueError
@pytest.mark.parametrize("code", [
    "", "SAVE0", "SAVE51", "DISCOUNT10", "save-5",
    "SAVEX10"
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- test shipping_fee ---------
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# Negative subtotal should raise ValueError
with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- test Cart class ---------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item and items

def test_add_and_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple": 3}
    # Adding same item increases quantity but price must match
    c.add_item("apple", 2.0, 1)
    assert c.items() == {"apple": 4}
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0, 1)  # different price

# Validation errors for add_item
@pytest.mark.parametrize("name,price,quantity", [
    ("orange", -1.0, 2),   # negative price
    ("pear", 1.5, 0),      # non‑positive quantity
])
def test_add_item_errors(empty_cart, name, price, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item(name, price, quantity)

# remove_item behavior

def test_remove_item(empty_cart):
    c = empty_cart
    c.add_item("banana", 1.0, 5)
    c.remove_item("banana", 2)
    assert c.items() == {"banana": 3}
    # Removing more than existing quantity removes item completely
    c.remove_item("banana", 5)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("cherry", 1)

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk(empty_cart):
    c = empty_cart
    # 10 apples -> 5% discount, unit price 1.0 => 9.50
    c.add_item("apple", 1.0, 10)
    assert c.subtotal() == 9.50
    # 55 oranges -> 10% discount, unit price 2.0 => 90.0
    c.add_item("orange", 2.0, 55)
    assert c.subtotal() == round(9.5 + 90.0, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping(empty_cart):
    c = empty_cart
    c.add_item("item", 200.0, 3)   # no bulk discount: 600.0
    # No coupon, non‑member => subtotal 600, shipping 60
    assert c.total(member=False) == round(600 + 60, 2)
    # With valid coupon SAVE10 -> reduce by 10%
    assert c.total(coupon="SAVE10", member=True) == round(
        (600 * 0.9) + cart.shipping_fee(600 * 0.9, True), 2
    )
    # Invalid coupon raises ValueError
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# total on empty cart is zero (no shipping)

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0.0
