import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper fixtures ----------
@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def populated_cart(empty_cart):
    empty_cart.add_item("apple", 100, quantity=5)   # subtotal 500
    empty_cart.add_item("banana", 200, quantity=3)  # subtotal 600, total 1100
    return empty_cart

# ---------- apply_discount tests ----------
def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
@ pytest.mark.parametrize("percent", [0, 50])
def test_apply_discount_price_error(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_error(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
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

@ pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_error(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@ pytest.mark.parametrize(
    "code",
    [
        "SAV10",       # missing 'E'
        "SAVE0",       # N < 1
        "SAVE51",      # N > 50
        "SAVE-5",      # negative
        "INVALID",     # unrelated string
        "  ",          # only whitespace
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999, False, 60),
        (1000, False, 0),
        (1500, True, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------
def test_cart_empty_total(empty_cart):
    assert empty_cart.total() == 0.0

def test_cart_subtotal(populated_cart):
    # apple: 5 * 100 = 500, banana: 3 * 200 = 600 -> subtotal 1100
    assert populated_cart.subtotal() == 1100

def test_cart_total_no_coupon_member(populated_cart):
    # subtotal 1100, member so shipping free (>=1000)
    assert populated_cart.total(member=True) == 1100.0

def test_cart_total_no_coupon_nonmember(populated_cart):
    # subtotal 1100, non-member but >=1000 so shipping free
    assert populated_cart.total() == 1100.0

def test_cart_total_with_coupon(populated_cart):
    # coupon SAVE10 -> 10% off subtotal
    expected = round(1100 * 0.9 + 60, 2) if 1100*0.9 < 1000 else round(1100 * 0.9, 2)
    assert populated_cart.total(coupon="SAVE10") == expected

# coupon invalid should raise
def test_cart_total_invalid_coupon(populated_cart):
    with pytest.raises(ValueError):
        populated_cart.total(coupon="INVALIDCODE")

# Adding and removing items affects subtotal correctly
def test_add_remove_items(empty_cart):
    empty_cart.add_item("widget", 250)
    assert empty_cart.subtotal() == 250
    empty_cart.remove_item("widget", quantity=1)
    assert empty_cart.subtotal() == 0
    # removing non-existent should not raise but keep zero
    empty_cart.remove_item("nonexistent")
    assert empty_cart.subtotal() == 0
