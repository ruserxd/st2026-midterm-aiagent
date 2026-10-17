import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Helper for floating comparison
def approx(v, eps=1e-9):
    return v if abs(v) < 1 else round(v, 10)

# --- apply_discount tests ---
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.99, 10, 90.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == approx(result)

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent", [-5, 105, 200]
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize(
    "quantity,expected",
    [
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

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --- parse_coupon tests ---
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

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "FAKE10", "save-5", "", "SAVExx"]
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, result):
    assert shipping_fee(subtotal, member=member) == result

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart tests ---
def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0

def test_add_and_remove_items():
    cart = Cart()
    cart.add_item("Apple", unit_price=100, quantity=2)
    cart.add_item("Banana", unit_price=50, quantity=1)
    assert cart.items() == {"Apple": 2, "Banana": 1}

    # Adding same item increases quantity and requires same price
    cart.add_item("Apple", unit_price=100, quantity=3)
    assert cart.items()["Apple"] == 5

    with pytest.raises(ValueError):
        cart.add_item("Apple", unit_price=90, quantity=1)  # price mismatch

    cart.remove_item("Apple", quantity=4)
    assert cart.items()["Apple"] == 1

    cart.remove_item("Banana")
    assert "Banana" not in cart.items()

    with pytest.raises(KeyError):
        cart.remove_item("Orange")

def test_subtotal_with_bulk_discount():
    cart = Cart()
    # 10 units at 100 -> bulk discount 5% -> each 95
    cart.add_item("Widget", unit_price=100, quantity=10)
    assert cart.subtotal() == round(100 * 10 * (1 - 0.05), 2)  # 950.0

    # Add another item with no discount
    cart.add_item("Gadget", unit_price=200, quantity=5)  # no bulk discount
    expected = 950 + 200 * 5
    assert cart.subtotal() == round(expected, 2)

def test_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("Book", unit_price=300, quantity=4)  # no bulk discount
    subtotal = 1200.0
    assert cart.subtotal() == subtotal

    # Coupon SAVE10 gives 10% off
    total_after_coupon = round(subtotal * (1 - 0.10), 2)
    shipping = 0 if total_after_coupon >= 1000 else 60
    expected_total = round(total_after_coupon + shipping, 2)
    assert cart.total(coupon="SAVE10") == expected_total

    # Member reduces shipping by half; but free shipping after coupon discount
    assert cart.total(member=True, coupon="SAVE10") == expected_total

    # No coupon: full subtotal
    shipping_fee_expected = 0 if subtotal >= 1000 else 60
    total_no_coupon = round(subtotal + shipping_fee_expected, 2)
    assert cart.total() == total_no_coupon

# Edge cases: empty cart has no shipping

def test_empty_cart_total():
    cart = Cart()
    assert cart.total(coupon="SAVE10") == 0.0

# Verify rounding behavior for fractional amounts

def test_rounding_behavior():
    cart = Cart()
    cart.add_item("Item", unit_price=99.999, quantity=1)
    # No discount; subtotal should be rounded to 2 decimals
    assert cart.subtotal() == round(99.999 * 1, 2)
    # Total with no shipping and no coupon
    assert cart.total() == round(cart.subtotal(), 2)
