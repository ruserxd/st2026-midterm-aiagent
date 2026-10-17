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


def test_apply_discount_rounding_and_bounds():
    # Rounding to two decimals
    assert apply_discount(199.999, 10) == pytest.approx(179.9991, rel=1e-9)
    # percent bounds
    with pytest.raises(ValueError):
        apply_discount(-1, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -5)
    with pytest.raises(ValueError):
        apply_discount(100, 105)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_values():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15


def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(2.5)  # non‑integer

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid_cases():
    for code, expected in [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE30 ", 30),
        ("sAvE1", 1),
        ("SaVe50", 50),
    ]:
        assert parse_coupon(code) == expected


def test_parse_coupon_invalid_cases():
    for bad in [
        "", "SAVE0", "SAVE51", "ABC10", "save-5", "SAVE10X", 123, None,
    ]:
        with pytest.raises(ValueError):
            parse_coupon(bad)

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    # members pay half
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(1200, member=True) == 0


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart ------------------------------------------------------------

@pytest.fixture
def empty_cart() -> Cart:
    return Cart()


def test_add_and_items(empty_cart: Cart):
    cart = empty_cart
    assert cart.items() == {}
    cart.add_item("apple", 2.5, quantity=3)
    assert cart.items() == {"apple": (2.5, 3)}
    cart.add_item("banana", 1.0)
    assert cart.items()["banana"] == (1.0, 1)


def test_remove_item(empty_cart: Cart):
    cart = empty_cart
    cart.add_item("apple", 2.0, quantity=5)
    cart.remove_item("apple", quantity=3)
    assert cart.items()["apple"] == (2.0, 2)
    # remove more than remaining -> remove fully
    cart.remove_item("apple", quantity=5)
    assert "apple" not in cart.items()
    with pytest.raises(KeyError):
        cart.remove_item("orange")


def test_subtotal(empty_cart: Cart):
    cart = empty_cart
    cart.add_item("a", 10, quantity=2)
    cart.add_item("b", 3.5, quantity=4)
    assert cart.subtotal() == 10 * 2 + 3.5 * 4


def test_total_without_discounts(empty_cart: Cart):
    cart = empty_cart
    cart.add_item("a", 100, quantity=2)  # subtotal 200
    assert cart.total(member=False, coupon=None) == pytest.approx(260.0)
    # shipping fee 60 + subtotal 200


def test_total_with_coupon_and_member(empty_cart: Cart):
    cart = empty_cart
    cart.add_item("widget", 500, quantity=1)
    # coupon SAVE10 -> 10% off on the subtotal before shipping
    total = cart.total(member=True, coupon="SAVE10")
    # expected: (500 * 0.9) + 30 shipping = 450 + 30 = 480
    assert total == pytest.approx(480.0)

# ---------- Bulk discount application via Cart --------------------------------

def test_bulk_discount_application(empty_cart: Cart):
    cart = empty_cart
    # buying 120 items triggers 15% bulk discount on that item
    cart.add_item("bulk", 10, quantity=120)
    total = cart.total()
    expected_subtotal = 10 * 120 * (1 - 0.15)  # bulk discount applied
    assert cart.subtotal() == pytest.approx(expected_subtotal)
    assert total == pytest.approx(expected_subtotal + 60)  # shipping still applies
