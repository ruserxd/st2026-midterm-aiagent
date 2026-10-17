import pytest
import cart

# ------------------- apply_discount ---------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Negative price should raise ValueError
def test_apply_discount_negative_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

# Percent out of range should raise ValueError
@pytest.mark.parametrize("price,percent", [(100, -5), (100, 105)])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------- bulk_discount_percent ---------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid quantity raises ValueError
@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------- parse_coupon ---------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30   ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupon formats raise ValueError
@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVEB", "10SAVE", "", "SA VE10"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------- shipping_fee ---------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0.0),
        (1200, True, 0.0),
        (999, False, 60.0),
        (999, True, 30.0),
        (500, True, 30.0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Negative subtotal raises ValueError
def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ------------------- Cart class ---------------------------------
# Helper to create a cart with known items

def make_cart_with_items(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

def test_cart_add_and_remove():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # Add same item again
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # Remove part of quantity
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}
    # Removing remaining removes item entirely
    c.remove_item("apple", 3)
    assert c.items() == {}

# Removing non-existent item raises KeyError
def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("banana", 1)

# Adding same item with different price raises ValueError

def test_cart_add_different_price():
    c = cart.Cart()
    c.add_item("orange", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.0, 1)

# Cart subtotal calculation (bulk discounts apply)
def test_cart_subtotal_basic():
    c = cart.Cart()
    c.add_item("itemA", 10.0, 5)   # 5 units => no bulk discount
    assert c.subtotal() == 50.00

# Bulk discount applied correctly
def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("itemB", 20.0, 10)  # 10 units => 5% bulk discount
    expected = round(20.0 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected

# Multiple items with different discounts
def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("small", 5.0, 9)   # no discount
    c.add_item("medium", 10.0, 15) # 5% discount
    c.add_item("large", 20.0, 55)  # 10% discount
    total = (
        5.0 * 9 +
        10.0 * 15 * (1 - 0.05) +
        20.0 * 55 * (1 - 0.10)
    )
    assert c.subtotal() == round(total, 2)

# Cart total without coupon or membership
def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    # subtotal 100, no shipping (since >1000?) but here 100 < 1000 so shipping 60
    expected = round(100.0 + 60.0, 2)
    assert c.total() == expected

# Cart total with member discount shipping half
def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item("item", 200.0, 1)  # subtotal 200
    # shipping fee 60 -> member pays 30
    expected = round(200.0 + 30.0, 2)
    assert c.total(member=True) == expected

# Cart total with coupon applied before shipping
def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    # subtotal 100, coupon SAVE10 => reduce by 10% -> 90
    # shipping fee on 90 is 60
    expected = round(90.0 + 60.0, 2)
    assert c.total(coupon="SAVE10") == expected

# Invalid coupon raises ValueError in total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 50.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Empty cart costs zero (no shipping)
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.0
