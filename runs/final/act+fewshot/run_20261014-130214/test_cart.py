import pytest
import cart

# Helper: round to two decimals as spec uses rounding in functions

def approx(x, tol=1e-9):
    return pytest.approx(x, abs=tol)

# Test apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == approx(result)

# Invalid values for apply_discount
@pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (60, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize("qty,percent", [
    (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

# Invalid quantity for bulk_discount_percent
@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Test parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save5", 5),
    ("  SaVe50  ", 50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# Invalid coupon codes
@pytest.mark.parametrize("code", ["SAVE0", "SAVEX", "10SAVE", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal,member,fee", [
    (1000, False, 0),
    (999.99, False, 60),
    (1200, True, 0),
    (10, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# Invalid subtotal for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 0.5, 3)
    assert c.items() == {"apple": 3}
    c.add_item("banana", 0.2, 2)
    assert c.items() == {"apple": 3, "banana": 2}
    # Adding more apples
    c.add_item("apple", 0.5, 1)
    assert c.items()["apple"] == 4

# Adding with different unit price raises

def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("orange", 0.3, 2)
    with pytest.raises(ValueError):
        c.add_item("orange", 0.4, 1)

# Removing items

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("cherry", 0.1, 5)
    c.remove_item("cherry", 3)
    assert c.items()["cherry"] == 2
    c.remove_item("cherry", 2)  # should remove entirely
    assert "cherry" not in c.items()

# Removing non-existent item raises KeyError

def test_cart_remove_missing():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("mango", 1)

# Subtotal calculation with bulk discounts

def test_cart_subtotal():
    c = cart.Cart()
    # 10 apples at $1 each - 5% discount
    c.add_item("apple", 1.0, 10)
    assert c.subtotal() == approx(9.5)  # 10 - 5%
    # Add 40 bananas at $2 each - no discount
    c.add_item("banana", 2.0, 40)
    # Banana subtotal: 80 (no discount)
    # Total should be 89.5
    assert c.subtotal() == approx(89.5)

# Total without coupon or membership

def test_cart_total_basic():
    c = cart.Cart()
    c.add_item("item", 1000, 1)  # no discount
    # Subtotal 1000, shipping free
    assert c.total() == approx(1000)

# Total with coupon and membership

def test_cart_total_coupon_member():
    c = cart.Cart()
    c.add_item("item", 200, 5)  # bulk discount: qty=5 -> no discount
    subtotal = 200 * 5
    assert c.subtotal() == approx(subtotal)
    total_before_shipping = subtotal
    coupon_discount = cart.parse_coupon("SAVE20")
    expected_after_coupon = cart.apply_discount(total_before_shipping, coupon_discount)
    shipping = cart.shipping_fee(expected_after_coupon, member=True)
    final_expected = round(expected_after_coupon + shipping, 2)
    assert c.total(member=True, coupon="SAVE20") == approx(final_expected)

# Empty cart total is zero (no shipping)

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.0
