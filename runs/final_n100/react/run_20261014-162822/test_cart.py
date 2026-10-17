import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Tests for apply_discount ---------------------------------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent --------------------------

def test_bulk_discount_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, -20])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon -----------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe5  ") == 5

@pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVE0", "SAVE51", "12345", "ABCD10", "SAVE -5", "SAVE50a"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Tests for shipping_fee -----------------------------------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200.5) == 0
    assert shipping_fee(999) == 60
    assert shipping_fee(800, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart ------------------------------------------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 60  # no items, non-member, shipping fee of 60

def test_add_and_remove_items():
    cart = Cart()
    cart.add_item("apple", 100, 2)
    cart.add_item("banana", 50)
    assert cart.items()["apple"] == (100, 2)
    assert cart.items()["banana"] == (50, 1)

    # removing part of quantity
    cart.remove_item("apple", 1)
    assert cart.items()["apple"] == (100, 1)

    # removing all quantity should delete the item
    cart.remove_item("apple")
    assert "apple" not in cart.items()

    # remove non-existent item raises KeyError
    with pytest.raises(KeyError):
        cart.remove_item("orange")

def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item("item1", 200, 3)   # subtotal 600
    cart.add_item("item2", 150, 7)   # subtotal +1050 => 1650 total before discounts

    # subtotal calculation
    assert cart.subtotal() == 1650

    # bulk discount: item1 quantity 3 -> no bulk discount; item2 qty 7 -> no bulk
    # No coupon, non-member
    expected_total = 1650 + shipping_fee(1650)
    assert cart.total() == expected_total

    # Apply a valid coupon for 10% discount
    assert cart.total(coupon="SAVE10") == round((1650 * 0.90) + shipping_fee(1650), 2)

    # Member should get half shipping
    member_total = (1650 * 0.90) + shipping_fee(1650, member=True)
    assert cart.total(coupon="SAVE10", member=True) == round(member_total, 2)

    # Invalid coupon raises ValueError
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")
