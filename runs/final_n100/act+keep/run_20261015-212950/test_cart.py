import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    shipping_fee,
    parse_coupon,
    Cart,
)

# Helper for invalid values
@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100.0, 25) == 75.0
    # rounding
    assert apply_discount(1.3333, 10) == round(1.3333 * 0.9, 2)

# bulk discount tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# shipping fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),
        (1000.00, False, 0),
        (1500, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# coupon parsing tests
valid_codes = ["SAVE10", "save50", "  SaVe15 "]
for code in valid_codes:
    def test_parse_coupon_valid(code=code):
        assert parse_coupon(code).isdigit() is False  # just placeholder

# Actually test specific values
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save50", 50),
    ("  SaVe15 ", 15),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVEXX", "123", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Cart tests

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", 1.00, 10)  # bulk discount 5%
    assert c.subtotal() == round(1.0*10 * (1-0.05), 2)
    c.add_item("banana", 2.0, 50)  # bulk discount 10%
    expected_total = (
        apply_discount(1.0*10, 5) +
        apply_discount(2.0*50, 10)
    )
    assert c.subtotal() == round(expected_total, 2)

def test_cart_add_duplicate_price():
    c = Cart()
    c.add_item("apple", 1.00, 5)
    # same price, should succeed
    c.add_item("apple", 1.00, 3)
    assert c.items()["apple"] == 8

def test_cart_add_duplicate_diff_price():
    c = Cart()
    c.add_item("apple", 1.00, 5)
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50, 2)

# invalid add
@pytest.mark.parametrize("unit_price,quantity", [(-1, 3), (2, 0), (2, -2)])
def test_cart_add_invalid(unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("apple", unit_price, quantity)

# remove tests

def test_cart_remove_item():
    c = Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 3)
    assert c.items()["apple"] == 2
    # removing more than remaining should delete item
    c.remove_item("apple", 5)
    assert "apple" not in c.items()

def test_cart_remove_nonexistent():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("banana")

# total calculation per spec

def test_cart_total_with_coupon_and_member_shipping():
    c = Cart()
    # 2 items to trigger shipping fee: subtotal 100
    c.add_item("item", 50.0, 2)
    amount_after_coupon = apply_discount(c.subtotal(), 10)  # coupon SAVE10
    expected_shipping = shipping_fee(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + expected_shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# test empty cart

def test_cart_empty_total():
    c = Cart()
    assert c.total() == 0
