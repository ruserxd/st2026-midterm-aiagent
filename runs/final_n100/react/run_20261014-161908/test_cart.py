import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- Helper data sets for parameterized tests -----
apply_cases = [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
]

@pytest.mark.parametrize("price,percent,expected", apply_cases)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-5.0, 10)])
def test_apply_discount_negative_price(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@pytest.mark.parametrize("price,percent", [(50.0, -1), (50.0, 101)])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ----- bulk_discount_percent tests -----
bulk_cases = [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (200, 15),
]

@pytest.mark.parametrize("quantity,expected", bulk_cases)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----- parse_coupon tests -----
valid_coupons = [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5  ", 5),
]

@pytest.mark.parametrize("code,expected", valid_coupons)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = ["NOPE10", "SAVE0", "SAVE51", "SAVEXX", " SAVE-5 "]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- shipping_fee tests -----
sf_cases = [
    (0.0, False, 60),
    (500.0, True, 30),
    (999.99, False, 60),
    (1000.0, False, 0),
    (1500.0, True, 0),
]

@pytest.mark.parametrize("subtotal,member,expected", sf_cases)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Cart class tests -----

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    # total uses subtotal and shipping only when no coupon
    assert c.total() == 60.0


def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", 10.0, quantity=2)
    assert c.items() == {"apple": (10.0, 2)}
    assert c.subtotal() == 20.0
    c.add_item("apple", 10.0, quantity=3)
    assert c.items()["apple"] == (10.0, 5)
    assert c.subtotal() == 50.0


def test_cart_remove_items():
    c = Cart()
    c.add_item("banana", 5.0, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items()["banana"] == (5.0, 2)
    with pytest.raises(ValueError):
        c.remove_item("banana", quantity=3)
    c.remove_item("banana", quantity=2)
    assert "banana" not in c.items()

# ----- total calculation tests -----
@pytest.mark.parametrize(
    "member,coupon,expected_total",
    [
        (False, None, 120.0),          # subtotal 100 + shipping 20 = 120
        (True, None, 110.0),           # subtotal 100 + half shipping 10 = 110
        (False, "SAVE5", 114.0),      # coupon reduces total by 5% of 120 = 6 -> 114
        (True, "save10", 99.0),       # subtotal 100 + half shipping 10 = 110; 10% off => 99
    ],
)
def test_cart_total_logic(member, coupon, expected_total):
    c = Cart()
    c.add_item("item", 20.0, quantity=5)   # subtotal 100
    total = c.total(member=member, coupon=coupon)
    assert round(total, 2) == round(expected_total, 2)

# Coupon ignored when cart empty

def test_cart_empty_with_coupon():
    c = Cart()
    assert c.total(coupon="SAVE10") == 60.0
