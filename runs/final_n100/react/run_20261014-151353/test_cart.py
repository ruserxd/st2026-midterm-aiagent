import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# ---------- Coupon parsing tests ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save50") == 50
    # surrounding whitespace ignored
    assert parse_coupon("   SaVe25  ") == 25

@pytest.mark.parametrize(
    "code",
    ["INVALID", "SAVE0", "SAVE51", "savelink", "", " SAVE-10 ", "save-5"],
)
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Discount application tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 10% of 99 = 9.9 -> result 89.1 rounded to 2 decimals
    assert apply_discount(99, 10) == 89.1

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize(
    "percent",
    [ -5, 105, 200],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Shipping fee tests ----------

def test_shipping_fee_free_over_threshold():
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000.50) == 0


def test_shipping_fee_regular_and_member():
    # non-member
    assert shipping_fee(999.99) == 60
    # member
    assert shipping_fee(999.99, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == []
    assert cart.subtotal() == 0
    assert cart.total() == 0


def test_add_and_remove_items():
    cart = Cart()
    cart.add_item("apple", 10, quantity=2)
    cart.add_item("banana", 5)
    # adding same item increments
    cart.add_item("apple", 10, quantity=3)
    expected_items = ["apple", "banana"]
    assert set(cart.items()) == set(expected_items)
    assert cart.subtotal() == (5 * 1) + (10 * 5)  # 5 + 50 = 55
    # remove some quantity
    cart.remove_item("apple", quantity=2)
    assert cart.subtotal() == (5 * 1) + (10 * 3)  # 5 + 30 = 35
    # remove remaining
    cart.remove_item("banana")
    assert "banana" not in cart.items()
    assert cart.subtotal() == 30


def test_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("item", 200, quantity=3)  # subtotal 600
    # Apply 20% coupon -> 480, shipping 60 => total 540
    assert cart.total(coupon="SAVE20") == 540.0
    # Member discount on shipping
    assert cart.total(member=True, coupon="SAVE20") == 510.0


def test_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("item", 100)
    with pytest.raises(ValueError):
        cart.total(coupon="badcode")

# ---------- Bulk discount percent function (not in spec, but included) ----------

def test_bulk_discount_percent_basic():
    # assume implementation: 1-10 ->0, >10 up to 20% etc.
    # We just check type and range
    from cart import bulk_discount_percent
    assert isinstance(bulk_discount_percent(5), int)
    assert 0 <= bulk_discount_percent(15) <= 100
