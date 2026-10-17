import pytest
import cart

# ---- Helper fixture for a fresh cart ----
@pytest.fixture
def empty_cart():
    return cart.Cart()

# ---- Tests for apply_discount ----
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.00),
    (100.0, 0, 100.00),
    (50.0, 100, 0.00),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Boundary and error cases for apply_discount
@pytest.mark.parametrize("price, percent", [
    (-1, 10),   # negative price
    (100, -5),  # percent < 0
    (100, 105), # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- Tests for bulk_discount_percent ----
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Error case for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- Tests for parse_coupon ----
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SAVE30   ", 30),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupons should raise ValueError
@pytest.mark.parametrize("code", [
    "save0",
    "SAVE51",
    "INVALID",
    "SAVEX",
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- Tests for shipping_fee ----
@pytest.mark.parametrize("subtotal, member, expected", [
    (0.0, False, 60),
    (999.99, True, 30),
    (1000.0, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Error case for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Tests for Cart class ----

def test_cart_add_and_items(empty_cart):
    c = empty_cart
    c.add_item("Apple", 0.50, 2)
    c.add_item("Banana", 0.30)
    assert c.items() == {"Apple": 2, "Banana": 1}

# Adding more of existing item must match unit_price

def test_cart_add_same_item_with_matching_price(empty_cart):
    c = empty_cart
    c.add_item("Orange", 0.80, 3)
    # same price should succeed
    c.add_item("Orange", 0.80, 2)
    assert c.items() == {"Orange": 5}

# Adding with different unit_price raises ValueError

def test_cart_add_same_item_different_price(empty_cart):
    c = empty_cart
    c.add_item("Grape", 1.00)
    with pytest.raises(ValueError):
        c.add_item("Grape", 1.20)

# Remove item and auto-removal when quantity reaches zero

def test_cart_remove_and_auto_remove(empty_cart):
    c = empty_cart
    c.add_item("Peach", 0.75, 3)
    # remove one
    c.remove_item("Peach", 1)
    assert c.items() == {"Peach": 2}
    # remove two more -> item removed
    c.remove_item("Peach", 2)
    assert c.items() == {}

# Removing non-existent item raises KeyError

def test_cart_remove_nonexistent(empty_cart):
    c = empty_cart
    with pytest.raises(KeyError):
        c.remove_item("NonExistent")

# Subtotal calculation

def test_cart_subtotal(empty_cart):
    c = empty_cart
    c.add_item("Milk", 2.50, 4)
    c.add_item("Bread", 1.20, 2)
    assert c.subtotal() == pytest.approx(2.5*4 + 1.2*2)

# Total calculation with member and coupon

def test_cart_total_member_and_coupon(empty_cart):
    c = empty_cart
    c.add_item("Soda", 1.50, 10)   # quantity >=10 gives 5% bulk discount on unit price
    subtotal_expected = 1.50 * 10
    discounted_unit_price = cart.apply_discount(1.50, 5)
    total_after_bulk = discounted_unit_price * 10
    shipping = cart.shipping_fee(total_after_bulk, member=True)  # free if >=1000? no
    coupon_percent = cart.parse_coupon("SAVE20")
    discount_on_total = total_after_bulk * (coupon_percent/100)
    expected_total = total_after_bulk - discount_on_total + shipping
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(expected_total)

# Total calculation without member and no coupon

def test_cart_total_simple(empty_cart):
    c = empty_cart
    c.add_item("Book", 12.00, 1)
    assert c.total() == 12.00 + 60  # shipping fee of 60 for subtotal <1000
