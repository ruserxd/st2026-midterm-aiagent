import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---- apply_discount -------------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    assert apply_discount(99.999, 10) == round(99.999 * 0.90, 2)


def test_apply_discount_zero_and_full_percent():
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)


def test_apply_discount_invalid_percent():
    for bad in [-1, 101]:
        with pytest.raises(ValueError):
            apply_discount(100, bad)

# ---- bulk_discount_percent -------------------------------------------------

def test_bulk_discount_percent_cases():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15


def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)
    with pytest.raises(ValueError):
        bulk_discount_percent(4.5)

# ---- parse_coupon ---------------------------------------------------------

def test_parse_coupon_valid_codes():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("  SAVE5") == 5


def test_parse_coupon_invalid():
    for code in ["", "SAVExx", "SAVE0", "SAVE51", "INVALID"]:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---- shipping_fee ---------------------------------------------------------

def test_shipping_fee_cases():
    assert shipping_fee(1000) == 0.0
    assert shipping_fee(999, member=False) == 60.0
    assert shipping_fee(999, member=True) == 30.0
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---- Cart class ----------------------------------------------------------

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == {}
    cart.add_item("apple", 1.0, quantity=3)
    assert cart.items() == {"apple": (1.0, 3)}
    cart.remove_item("apple", quantity=1)
    assert cart.items()["apple"] == (1.0, 2)


def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item("pen", 5.0, quantity=2)   # subtotal 10
    cart.add_item("notebook", 12.5, quantity=1)  # subtotal now 22.5
    assert cart.subtotal() == 22.5
    total = cart.total()
    expected_total = 22.5 + (60 if 22.5 < 1000 else 0)
    assert total == expected_total


def test_cart_with_coupon_and_member():
    cart = Cart()
    cart.add_item("widget", 40, quantity=2)   # subtotal 80
    total = cart.total(member=True, coupon="SAVE20")
    discounted_subtotal = apply_discount(80, 20)
    expected_total = discounted_subtotal + (30 if 80 < 1000 else 0)
    assert total == expected_total
