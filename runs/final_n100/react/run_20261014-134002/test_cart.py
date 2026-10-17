import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ---------------------------------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 10% of 99 is 9.9 -> 89.1
    assert apply_discount(99, 10) == 89.1


def test_apply_discount_zero_percent():
    assert apply_discount(50, 0) == 50.0


def test_apply_discount_full_percent():
    assert apply_discount(80, 100) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        apply_discount(50, -5)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        apply_discount(50, 150)

# ---------- bulk_discount_percent ---------------------------------

def test_bulk_discount_percent_low_quantity():
    assert bulk_discount_percent(1) == 0


def test_bulk_discount_percent_ten_units():
    assert bulk_discount_percent(10) == 5


def test_bulk_discount_percent_fifty_units():
    assert bulk_discount_percent(50) == 10


def test_bulk_discount_percent_hundred_units():
    assert bulk_discount_percent(100) == 15


def test_bulk_discount_percent_above_hundred():
    assert bulk_discount_percent(150) == 15


def test_bulk_discount_percent_invalid_zero():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)


def test_bulk_discount_percent_negative():
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

# ---------- parse_coupon ---------------------------------

def test_parse_coupon_valid_simple():
    assert parse_coupon("SAVE10") == 10


def test_parse_coupon_case_insensitive_and_whitespace():
    assert parse_coupon("  save25 ") == 25


def test_parse_coupon_invalid_prefix():
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")


def test_parse_coupon_invalid_suffix():
    with pytest.raises(ValueError):
        parse_coupon("SAVEAB")


def test_parse_coupon_out_of_range_low():
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")


def test_parse_coupon_out_of_range_high():
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")

# ---------- shipping_fee ---------------------------------

def test_shipping_fee_above_threshold():
    assert shipping_fee(1200) == 0


def test_shipping_fee_below_threshold_non_member():
    assert shipping_fee(500) == 60


def test_shipping_fee_below_threshold_member():
    assert shipping_fee(400, member=True) == 30


def test_shipping_fee_exact_threshold():
    assert shipping_fee(1000) == 0


def test_shipping_fee_negative_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart ---------------------------------

def test_cart_initial_state():
    cart = Cart()
    assert list(cart.items()) == []
    assert cart.subtotal() == 0
    assert cart.total() == 60  # subtotal 0, non-member, no coupon


def test_add_item_and_subtotal():
    cart = Cart()
    cart.add_item("apple", 100, quantity=3)
    assert cart.items() == {"apple": (100, 3)}
    assert cart.subtotal() == 300


def test_remove_item_decreases_quantity():
    cart = Cart()
    cart.add_item("banana", 50, quantity=5)
    cart.remove_item("banana", quantity=2)
    assert cart.items()["banana"] == (50, 3)
    assert cart.subtotal() == 150


def test_remove_item_entirely_when_quantity_zero():
    cart = Cart()
    cart.add_item("orange", 30, quantity=2)
    cart.remove_item("orange", quantity=2)
    assert "orange" not in cart.items()
    assert cart.subtotal() == 0


def test_total_with_bulk_discount_and_shipping():
    # 10 apples at $10 each -> subtotal 100, bulk discount 5% -> 95
    cart = Cart()
    cart.add_item("apple", 10, quantity=10)
    assert cart.total(member=False) == 155.0  # 95 + 60 shipping


def test_total_with_member_shipping_and_coupon():
    cart = Cart()
    cart.add_item("widget", 200, quantity=2)  # subtotal 400, bulk discount 0% -> 400
    total = cart.total(member=True, coupon="SAVE10")
    # subtotal after 10% off => 360; shipping half of 60 =>30; final 390
    assert total == 390.0

# Edge cases for Cart operations

def test_add_item_non_integer_quantity():
    cart = Cart()
    with pytest.raises(TypeError):
        cart.add_item("gadget", 100, quantity="three")


def test_remove_more_than_existing_quantity_raises():
    cart = Cart()
    cart.add_item("tool", 50, quantity=1)
    with pytest.raises(ValueError):
        cart.remove_item("tool", quantity=2)
