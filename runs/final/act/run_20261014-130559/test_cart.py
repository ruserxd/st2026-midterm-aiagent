import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# --- Tests for apply_discount ---

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # price that leads to more than 2 decimals after discount
    assert apply_discount(199.99, 10) == round(199.99 * (1 - 0.10), 2)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-5, 20)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        apply_discount(100, -1)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        apply_discount(100, 101)

# --- Tests for bulk_discount_percent ---

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15


def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        bulk_discount_percent(0)

# --- Tests for parse_coupon ---

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe5 ") == 5


def test_parse_coupon_invalid_range():
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        parse_coupon("SAV10")
    with pytest.raises(ValueError):
        parse_coupon("SAVEx10")

# --- Tests for shipping_fee ---

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(800, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# --- Tests for Cart class behavior ---

def test_cart_initially_empty_and_add_item():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.5, quantity=3)
    assert c.items() == {"apple": (1.5, 3)}


def test_cart_remove_item_partial_and_full():
    c = Cart()
    c.add_item("banana", 0.5, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items()["banana"] == (0.5, 2)
    c.remove_item("banana", quantity=2)
    assert "banana" not in c.items()


def test_cart_subtotal_and_total_with_member_and_coupon():
    c = Cart()
    c.add_item("widget", 100, quantity=10)   # bulk discount 5%
    subtotal_expected = apply_discount(100 * 10, 5)
    assert c.subtotal() == subtotal_expected

    total_no_fee = subtotal_expected + shipping_fee(subtotal_expected)
    assert round(c.total(member=False), 2) == round(total_no_fee, 2)

    total_member_half_fee = subtotal_expected + shipping_fee(subtotal_expected, member=True)
    assert round(c.total(member=True), 2) == round(total_member_half_fee, 2)

    # coupon of 10% on the final total (after shipping)
    coupon_code = "SAVE10"
    total_with_coupon = apply_discount(total_no_fee, parse_coupon(coupon_code))
    assert round(c.total(member=False, coupon=coupon_code), 2) == round(total_with_coupon, 2)

# End of test_cart.py
