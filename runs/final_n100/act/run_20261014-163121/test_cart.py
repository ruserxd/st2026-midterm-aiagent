import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize(
    "percent",
    [-5, 101, 150]
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------------------------------------

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@ pytest.mark.parametrize(
    "code",
    ["", "SAVEBAD", "SAVE0", "SAVE51", "12345", "XSAVE10"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

def test_shipping_fee_member():
    assert shipping_fee(50, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class -----------------------------------------------------

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == {}

    cart.add_item("apple", 2.5, 3)
    assert cart.items() == {"apple": (2.5, 3)}
    assert cart.subtotal() == 7.5

    cart.add_item("banana", 1.0)
    assert cart.items()["banana"] == (1.0, 1)
    assert cart.subtotal() == 8.5

    cart.remove_item("apple", 2)
    assert cart.items()["apple"] == (2.5, 1)
    assert cart.subtotal() == 6.0

    # Removing more than present should reduce to zero quantity and remove key
    cart.remove_item("banana", 5)
    assert "banana" not in cart.items()
    assert cart.subtotal() == 2.5


def test_cart_total_with_discounts_and_coupon():
    cart = Cart()
    cart.add_item("widget", 10, 120)   # bulk discount applies

    subtotal = cart.subtotal()  # 1200
    assert subtotal == 1200

    # Without member or coupon
    total_no_member = cart.total(member=False)
    # Bulk discount 15% on each item? bulk_discount_percent for quantity=120 -> 15%
    discounted_unit = apply_discount(10, 15)  # 8.5
    expected_subtotal_after_bulk = 8.5 * 120  # 1020
    shipping = shipping_fee(expected_subtotal_after_bulk)
    assert total_no_member == round(expected_subtotal_after_bulk + shipping, 2)

    # Member pays half shipping
    total_member = cart.total(member=True)
    expected_total_member = round(
        expected_subtotal_after_bulk + shipping / 2,
        2
    )
    assert total_member == expected_total_member

    # Coupon with discount percent applied after bulk and member shipping
    cart.add_item("gadget", 5, 1)  # no bulk
    total_with_coupon = cart.total(member=False, coupon="SAVE10")
    # compute manually
    # current subtotal before coupon
    current_subtotal = cart.subtotal()
    discounted_current = apply_discount(current_subtotal, 10)
    shipping_after_coupon = shipping_fee(discounted_current)
    expected_total_coupon = round(discounted_current + shipping_after_coupon, 2)
    assert total_with_coupon == expected_total_coupon

# ---------- Edge cases -----------------------------------------------------

def test_cart_negative_and_zero_prices():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", -1, 5)
    with pytest.raises(ValueError):
        cart.add_item("zero", 0, 2)  # unit price zero should be allowed? spec unclear

# Test that bulk discount is applied per-item in total calculation
# already covered above.
