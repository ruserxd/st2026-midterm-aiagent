import pytest
import cart

# ---------- apply_discount tests ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.00),   # basic example from spec
    (100, 0, 100.00),    # no discount
    (50, 100, 0.00),     # full discount
])
def test_apply_discount_basic(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases for errors
@pytest.mark.parametrize("price,percent", [
    (-1, 10),            # negative price
    (100, -5),           # negative percent
    (100, 150),          # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize("quantity,percent", [
    (9, 0),              # below threshold
    (10, 5),             # >=10
    (49, 5),             # just below 50
    (50, 10),            # >=50
    (99, 10),            # just below 100
    (100, 15),           # >=100
])
def test_bulk_discount_percent_basic(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# Error cases for non-positive or non-integer quantities
@pytest.mark.parametrize("quantity", [0, -5, 3.7, "10"])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25", 25),
    ("   SaVe5   ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "",
    "SAVE0",          # N < 1
    "SAVE51",         # N > 50
    "DISCOUNT10",
    "save-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize("subtotal,fee", [
    (0, 60),            # below free threshold
    (500, 60),          # any non-free subtotal
    (1000, 0),          # exactly free
    (1500, 0),          # above free
])
def test_shipping_fee_basic(subtotal, fee):
    assert cart.shipping_fee(subtotal) == fee

# Member gets half the fee when not free
@pytest.mark.parametrize("subtotal", [500, 999.99])
def test_shipping_fee_member_half(subtotal):
    assert cart.shipping_fee(subtotal, member=True) == 30

# Errors for negative subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------
# Helper to create a simple cart

def create_cart(items):
    """Return a cart populated with given items.
    items: list of tuples (name, unit_price, quantity)
    """
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# Test adding and item quantity accumulation

def test_cart_add_and_accumulate():
    c = create_cart([("apple", 1.0, 2)])
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 5}

# Test error when adding same item with different price

def test_cart_add_different_price():
    c = cart.Cart()
    c.add_item("banana", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 3.0, 1)

# Test removing items

def test_cart_remove_items():
    c = create_cart([("orange", 0.5, 4)])
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 2}
    c.remove_item("orange", 2)
    assert "orange" not in c.items()

# Test removing non-existent item raises KeyError

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# Test subtotal calculation with bulk discounts

def test_cart_subtotal_with_bulk_discount():
    # 10 items of $2 each => 5% discount on that item
    c = create_cart([("item", 2.0, 10)])
    expected = round(2.0 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected

# Test subtotal with multiple items and different discounts

def test_cart_subtotal_multiple_items():
    # 5 items at $3 each => no discount; 15 items at $4 each => 5% discount
    c = create_cart([("a", 3.0, 5), ("b", 4.0, 15)])
    subtotal_a = 3.0 * 5  # 15.00
    subtotal_b = round(4.0 * 15 * (1 - 0.05), 2)  # 57.0
    assert c.subtotal() == round(subtotal_a + subtotal_b, 2)

# Test total calculation with coupon and shipping

def test_cart_total_with_coupon_and_shipping():
    c = create_cart([("item", 100.0, 1)])
    # Subtotal: 100; apply coupon 10% => 90; shipping fee 60 => total 150
    assert c.total(coupon="SAVE10") == 150.00

# Test total for member discount on shipping only

def test_cart_total_member_shipping():
    c = create_cart([("item", 200.0, 1)])
    # Subtotal 200; no coupon; shipping fee free (>=1000)
    assert c.total(member=True) == 200.00

# Test total for empty cart returns 0 without shipping

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.00
