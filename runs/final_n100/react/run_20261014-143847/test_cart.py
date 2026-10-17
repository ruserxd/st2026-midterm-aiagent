import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# Helper: round to cents
round2 = lambda x: round(x + 1e-8, 2)

# Test coupon parsing and application
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("HALFOFF", 50),
        ("15PERCENT", 15),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# Test invalid coupon raises ValueError
@pytest.mark.parametrize("code", ["", "abc", "10%OFF"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Shipping fee tests (subtotal after coupon is used as argument)
@pytest.mark.parametrize(
    "subtotal, member, expected_fee",
    [
        (0, False, 0),          # empty cart no shipping
        (30, False, 10),        # under threshold
        (30, True, 5),          # member discount on fee
        (200, False, 20),       # over threshold
    ],
)
def test_shipping_fee(subtotal, member, expected_fee):
    assert shipping_fee(subtotal, member) == expected_fee

# Bulk discount percent tests
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
        (5, 0),
        (10, 5),
        (25, 5),
        (30, 10),
        (100, 10),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# Test apply_discount function directly
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100, 0, 100),
        (100, 10, 90),
        (250.75, 5, 238.19),
    ],
)
def test_apply_discount(price, percent, expected):
    # Use rounding to avoid floating point issues
    assert round2(apply_discount(price, percent)) == round2(expected)

# Test Cart functionality: subtotal and items
@pytest.mark.parametrize(
    "items, expected_subtotal",
    [
        ([], 0),
        ([("apple", 1.5)], 1.5),
        ([("banana", 0.75, 3)] , 2.25),
        ([("cherry", 2.0, 4), ("date", 3.0, 2)], 20.0),
    ],
)
def test_cart_subtotal_and_items(items, expected_subtotal):
    c = Cart()
    for item in items:
        if len(item) == 2:
            name, price = item
            c.add_item(name, price)
        else:
            name, price, qty = item
            c.add_item(name, price, qty)
    assert round2(c.subtotal()) == round2(expected_subtotal)
    # items() should reflect added quantities
    for name, price, *rest in [(*i[:2], i[2] if len(i) > 2 else 1) for i in items]:
        qty = rest[0]
        assert any(entry["name"] == name and entry["quantity"] == qty and entry["unit_price"] == price for entry in c.items())

# Test Cart total with coupon, shipping, member flag
@pytest.mark.parametrize(
    "items, coupon_code, member, expected_total",
    [
        # No items: 0
        ([], None, False, 0),
        # Items without discount
        ([("apple", 10.0, 2)], None, False, 30),  # subtotal=20 + shipping(10)=30
        # Items with coupon reduce price before shipping
        ([("banana", 5.0, 4)], "SAVE10", False, 18),
        # Member discount on shipping
        ([("cherry", 15.0, 1)], None, True, 20),  # subtotal=15 + shipping(5)=20
        # Coupon that reduces to zero subtotal (e.g., huge coupon)
        ([("date", 20.0, 1)], "HALFOFF", False, 25),
    ],
)
def test_cart_total(items, coupon_code, member, expected_total):
    c = Cart()
    for item in items:
        if len(item) == 2:
            name, price = item
            c.add_item(name, price)
        else:
            name, price, qty = item
            c.add_item(name, price, qty)
    total = c.total(member=member, coupon=coupon_code)
    assert round(total, 2) == expected_total

# Test that removing items updates subtotal correctly

def test_cart_remove_and_subtotal():
    c = Cart()
    c.add_item("apple", 1.5, 3)   # 4.5
    c.add_item("banana", 0.75, 2) # 1.5 total 6.0
    assert round(c.subtotal(), 2) == 6.0
    c.remove_item("apple", 1)
    assert round(c.subtotal(), 2) == 4.5
    c.remove_item("banana")
    assert round(c.subtotal(), 2) == 3.75
    # Removing more than existing should remove item entirely
    c.remove_item("apple", 10)
    assert all(entry["name"] != "apple" for entry in c.items())
    assert round(c.subtotal(), 2) == 0

# Test that total with invalid coupon raises ValueError

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("item", 10)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
