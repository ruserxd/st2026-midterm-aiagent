import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),          # example from spec
        (100, 0, 100.0),            # no discount
        (123.45, 50, 61.73),       # half price rounded to 2 decimals
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [
        (-10, 5),                   # negative price
        (50, -5),                   # negative percent
        (30, 110),                  # percent > 100
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --- bulk_discount_percent ---------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
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
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "",                # empty string
    "SAVE0",          # below lower bound
    "SAVE51",         # above upper bound
    "DISCOUNT10",     # wrong prefix
    "save-5",        # negative number
    "save ten",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee ------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000.0, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart integration tests --------------------------------------------
def test_cart_empty_total():
    c = Cart()
    assert c.total() == 0.00

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", 1.50, quantity=10)   # triggers 5% bulk discount
    # discounted unit price: 1.50 * 0.95 = 1.425 => round to 2 decimals per item? subtotal should be rounded at end.
    expected_subtotal = round(1.50 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected_subtotal

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("widget", 200, quantity=5)   # no bulk discount
    # subtotal: 1000
    # coupon SAVE10 reduces to 900
    # shipping fee: since 900 < 1000 and non-member => 60
    assert c.total(coupon="SAVE10") == round(900 + 60, 2)

def test_cart_total_member_shipment_free():
    c = Cart()
    c.add_item("premium", 400, quantity=3)   # subtotal 1200
    # coupon SAVE20 -> 960
    # shipping: member, 960<1000 => 30
    assert c.total(member=True, coupon="SAVE20") == round(960 + 30, 2)

# Test removal and updates
def test_cart_remove_and_total():
    c = Cart()
    c.add_item("book", 12.99, quantity=15)   # bulk discount 5%
    c.remove_item("book", quantity=5)       # remaining 10 units -> still bulk discount 5%
    expected_subtotal = round(12.99 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected_subtotal
    # total without coupon: subtotal + shipping (since <1000, member False) => +60
    assert c.total() == round(expected_subtotal + 60, 2)
