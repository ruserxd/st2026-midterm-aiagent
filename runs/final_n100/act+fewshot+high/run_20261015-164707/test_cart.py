import pytest
import cart

# Test apply_discount for valid inputs
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (500, 100, 0.0),
    (0, 50, 0.0)
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Test apply_discount for invalid inputs
@pytest.mark.parametrize("price,percent", [
    (-10, 20),   # negative price
    (100, -5),   # negative percent
    (100, 105)   # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent boundary at 50
def test_bulk_discount_percent_boundary():
    assert cart.bulk_discount_percent(50) == 10

@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (51, 10),
    (100, 15),
    (150, 15)
])
def test_bulk_discount_percent_values(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Test parse_coupon with valid codes including case-insensitivity and whitespace handling
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("  SAVE20  ", 20),
    ("save30", 30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Test parse_coupon with invalid codes
@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVEXX",
    "",
    None,
    1234
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee for various subtotals and membership status
@pytest.mark.parametrize("subtotal,member,expected", [
    (999, False, 60),
    (999, True, 30),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Test Cart.add_item and items method
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 0.5, 2)
    assert c.items() == {"apple": 2}
    # Add same item increases quantity
    c.add_item("apple", 0.5, 3)
    assert c.items() == {"apple": 5}
    # Different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 0.6, 1)
    # Negative unit_price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("orange", -1.0, 1)
    # Zero or negative quantity raises ValueError
    for bad_qty in [0, -5]:
        with pytest.raises(ValueError):
            c.add_item("banana", 1.0, bad_qty)
    # Non-integer quantity raises ValueError
    with pytest.raises(ValueError):
        c.add_item("grape", 2.0, 1.5)

# Test Cart.remove_item and that zero-quantity items are removed entirely
def test_cart_remove_and_items_zero_removal():
    c = cart.Cart()
    c.add_item("pen", 1.0, 4)
    # Remove part of quantity
    c.remove_item("pen", 2)
    assert c.items() == {"pen": 2}
    # Removing remaining equal quantity should remove the item completely
    c.remove_item("pen", 2)
    assert c.items() == {}
    # Removing more than present also removes the item
    c.add_item("staple", 0.5, 3)
    c.remove_item("staple", 10)
    assert c.items() == {}

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# Test Cart.subtotal for empty and with bulk discounts
def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    # itemA: price=10.1, qty=10 -> discount 5%
    c.add_item("itemA", 10.1, 10)
    # itemB: price=20.2, qty=10
    c.add_item("itemB", 20.2, 10)
    expected = round(95.95 + 191.9, 2)  # 287.85
    assert c.subtotal() == expected

# Test Cart.total for various scenarios
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_non_member_no_coupon():
    c = cart.Cart()
    c.add_item("widget", 200, 1)
    # subtotal 200 + shipping 60 => 260
    assert c.total(member=False) == 260.0

def test_cart_total_member_no_coupon():
    c = cart.Cart()
    c.add_item("widget", 200, 1)
    # subtotal 200 + shipping 30 => 230
    assert c.total(member=True) == 230.0

# Cart.total with coupon that reduces subtotal below free shipping threshold (non-member)
def test_cart_total_with_coupon_free_shipping_after_discount():
    c = cart.Cart()
    c.add_item("expensive", 1100, 1)
    discounted_amount = round(cart.apply_discount(1100, 10), 2)  # 990.0
    expected_shipping = 60 if discounted_amount < 1000 else 0
    expected_total = round(discounted_amount + expected_shipping, 2)
    assert c.total(member=False, coupon="SAVE10") == expected_total

# Cart.total with coupon that reduces subtotal below free shipping threshold (member)
def test_cart_total_with_coupon_free_shipping_after_discount_member():
    c = cart.Cart()
    c.add_item("expensive", 1100, 1)
    discounted_amount = round(cart.apply_discount(1100, 10), 2)  # 990.0
    expected_shipping = 30 if discounted_amount < 1000 else 0
    expected_total = round(discounted_amount + expected_shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# Cart.total with invalid coupon raises ValueError
def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("widget", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# parse_coupon type error for non-string input
def test_parse_coupon_non_string():
    with pytest.raises(ValueError):
        cart.parse_coupon(1234)
