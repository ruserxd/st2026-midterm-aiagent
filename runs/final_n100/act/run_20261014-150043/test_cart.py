import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- Tests for apply_discount -----

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 100 with 33% -> 67.0 (exactly 2 decimals)
    assert apply_discount(100, 33) == 67.0
    # 99 with 33% -> 66.33
    assert apply_discount(99, 33) == 66.33


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        apply_discount(100, -5)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        apply_discount(100, 105)

# ----- Tests for bulk_discount_percent -----

def test_bulk_discount_percent_edge_cases():
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(99) == 10


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(2.5)  # not an int

# ----- Tests for parse_coupon -----

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        parse_coupon("INVALID")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")   # below min
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # above max
    with pytest.raises(ValueError):
        parse_coupon("SA VE10")

# ----- Tests for shipping_fee -----

def test_shipping_fee_free_threshold():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.75) == 0


def test_shipping_fee_standard_and_member():
    assert shipping_fee(999) == 60
    assert shipping_fee(50, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ----- Tests for Cart class -----

def test_cart_initial_empty():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 60  # no items, subtotal=0 -> shipping 60


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=2)
    c.add_item("banana", unit_price=50)
    assert c.items() == {"apple": (100, 2), "banana": (50, 1)}
    assert c.subtotal() == 100*2 + 50
    # remove one banana -> should raise because only 1
    with pytest.raises(KeyError):
        c.remove_item("banana", quantity=2)
    c.remove_item("banana")
    assert "banana" not in c.items()
    # Remove part of apple qty
    c.remove_item("apple", quantity=1)
    assert c.items()["apple"] == (100, 1)


def test_cart_total_with_discount_and_coupon():
    cart = Cart()
    cart.add_item("item", unit_price=200, quantity=10)  # bulk discount 5%
    subtotal_before = cart.subtotal()  # 2000
    expected_bulk_disc = apply_discount(subtotal_before, bulk_discount_percent(10))
    assert expected_bulk_disc == 1900.0
    shipping = shipping_fee(expected_bulk_disc)
    total_no_coupon = expected_bulk_disc + shipping
    assert cart.total(member=True) == pytest.approx(total_no_coupon - shipping/2)
    # Apply a coupon of 20%
    total_with_coupon = apply_discount(expected_bulk_disc, 20) + shipping
    assert cart.total(coupon="SAVE20") == pytest.approx(total_with_coupon)

# ----- Edge case: very large quantity for bulk discount -----
def test_cart_bulk_discount_high_quantity():
    cart = Cart()
    cart.add_item("bulk", unit_price=10, quantity=150)  # should get 15%
    subtotal = 1500
    discounted = apply_discount(subtotal, bulk_discount_percent(150))
    assert discounted == 1275.0

# ----- Test that parse_coupon is case-insensitive and trims whitespace -----
def test_parse_coupon_edge_whitespace_and_case():
    assert parse_coupon("   SaVe15 ") == 15
