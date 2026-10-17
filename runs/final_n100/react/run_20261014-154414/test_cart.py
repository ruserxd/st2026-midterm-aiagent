import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- helper fixtures ----------
@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def sample_cart(empty_cart):
    # Add two items with varying quantities
    empty_cart.add_item("apple", unit_price=100, quantity=5)   # 500
    empty_cart.add_item("banana", unit_price=200, quantity=12)  # 2400
    return empty_cart

# ---------- tests for apply_discount ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(1000, 0) == 1000.0
    assert apply_discount(1234.56, 100) == 0.0
    # ensure rounding to two decimals
    assert apply_discount(99.999, 10) == 90.0

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -5)
    with pytest.raises(ValueError):
        apply_discount(100, 150)

# ---------- tests for bulk_discount_percent ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-10)

# ---------- tests for parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save25 ") == 25
    assert parse_coupon("SaVe5") == 5

def test_parse_coupon_errors():
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")   # below allowed range
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # above allowed range
    with pytest.raises(ValueError):
        parse_coupon(" SAVE-5 ")
    with pytest.isin(['', 'SAVEX']):
        pass

# ---------- tests for shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(99.99) == 60
    assert shipping_fee(100) == 60
    assert shipping_fee(999.99) == 60
    # free for >=1000
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0


def test_shipping_fee_member():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=True) == 0


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- tests for Cart methods ----------

def test_cart_add_and_remove(empty_cart):
    empty_cart.add_item("tshirt", unit_price=200, quantity=2)  # 400
    assert empty_cart.subtotal() == 400
    empty_cart.remove_item("tshirt", quantity=1)
    assert empty_cart.subtotal() == 200
    # remove last
    empty_cart.remove_item("tshirt")
    assert empty_cart.items() == []


def test_cart_bulk_discount(sample_cart):
    # apple: 5 units -> no bulk discount
    # banana: 12 units -> 5% discount per item
    # compute expected subtotal with discounts applied by add_item logic
    # the cart implementation applies bulk_discount_percent when adding items
    assert sample_cart.subtotal() == 500 + 2400 * 0.95


def test_cart_total_without_coupon_or_member(sample_cart):
    amount_before_shipping = sample_cart.subtotal()
    expected = round(amount_before_shipping + shipping_fee(amount_before_shipping), 2)
    assert sample_cart.total() == expected


def test_cart_total_with_coupon_and_member(sample_cart):
    # Use coupon SAVE10 (10% off)
    amount_after_discount = apply_discount(sample_cart.subtotal(), parse_coupon("SAVE10"))
    shipping = shipping_fee(amount_after_discount, member=True)
    total_expected = round(amount_after_discount + shipping, 2)
    assert sample_cart.total(member=True, coupon="SAVE10") == total_expected


def test_cart_total_invalid_coupon(sample_cart):
    with pytest.raises(ValueError):
        sample_cart.total(coupon="INVALID")


def test_empty_cart_total():
    c = Cart()
    assert c.total() == 0.0
