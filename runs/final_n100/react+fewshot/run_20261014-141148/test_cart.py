import pytest
import cart

# Helper to compare floats with rounding as per spec

def round2(x):
    return round(float(x), 2)

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Invalid inputs for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (50, -5),
    (50, 105),
])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (20, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid quantity
@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("SaVe5", 5),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

# Invalid coupon codes
@pytest.mark.parametrize("code", ["SAVE0", "SAVEX", "10SAVE", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (1200, False, 0),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Invalid subtotal
@pytest.mark.parametrize("subtotal", [-5, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 0.5, 2)
    assert c.items() == {"apple": (1.0, 3), "banana": (0.5, 2)}

# Adding same item increases quantity

def test_cart_add_existing_increases_quantity():
    c = cart.Cart()
    c.add_item("apple", 1.0, 2)
    c.add_item("apple", 1.0, 3)
    assert c.items()["apple"] == (1.0, 5)

# Adding with different price raises ValueError

def test_cart_add_different_price_error():
    c = cart.Cart()
    c.add_item("apple", 1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5, 1)

# Removing items

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 3)
    assert c.items()["apple"] == (1.0, 2)
    c.remove_item("apple", 2)
    assert "apple" not in c.items()

# Removing non-existent item raises KeyError

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear")

# Subtotal calculation

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.0, 2)  # $2
    c.add_item("banana", 0.5, 4)  # $2
    assert c.subtotal() == 4.0

# Total calculation with member and coupon

def test_cart_total_member_and_coupon():
    c = cart.Cart()
    c.add_item("apple", 1.0, 10)  # subtotal $10
    # bulk discount percent for 10 units is 5%
    expected_subtotal = 10.0
    bulk_discount = cart.bulk_discount_percent(10)
    discounted = cart.apply_discount(expected_subtotal, bulk_discount)
    shipping = cart.shipping_fee(discounted, member=True)  # half of 60 -> 30
    total_expected = round2(discounted + shipping)
    assert c.total(member=True, coupon="SAVE5") == total_expected

# Total calculation without member and no coupon

def test_cart_total_no_member_no_coupon():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    assert c.total() == 160.0  # $100 + shipping 60
