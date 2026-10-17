import pytest
from cart import (
    apply_discount,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Tests for helper functions -------------------------------------

def test_apply_discount_normal_and_rounding():
    # Basic discount
    assert apply_discount(200, 15) == 170.0
    # Rounding: 99.995 with 10% gives 90.0
    assert apply_discount(99.995, 10) == round(99.995 * 0.9, 2)


def test_apply_discount_errors():
    # negative price
    with pytest.raises(ValueError):
        apply_discount(-1, 20)
    # percent too low
    with pytest.raises(ValueError):
        apply_discount(100, -5)
    # percent too high
    with pytest.raises(ValueError):
        apply_discount(100, 105)


def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30


def test_parse_coupon_invalid_cases():
    for code in ["", "ABC10", "SAVEX", "SAVE0", "SAVE51", "SAVE-5", "123"]:
        with pytest.raises(ValueError):
            parse_coupon(code)


def test_shipping_fee_basic():
    # Subtotal >= 1000: free shipping
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.75) == 0
    # Below threshold, non-member
    assert shipping_fee(999) == 60
    assert shipping_fee(0) == 60


def test_shipping_fee_member_discount():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(100, member=True) == 30


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Tests for Cart class -------------------------------------------

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=2)  # 200
    c.add_item("banana", unit_price=50)              # 50
    assert c.subtotal() == 250


def test_cart_remove_and_subtotal():
    c = Cart()
    c.add_item("apple", 100, quantity=5)
    c.remove_item("apple", quantity=2)
    assert c.subtotal() == 300
    # Removing more than existing raises? implementation may allow but spec not clear.
    with pytest.raises(ValueError):
        c.remove_item("orange")


def test_cart_total_no_coupon_member_false():
    c = Cart()
    c.add_item("item", 500)
    # subtotal=500, shipping=60 (non-member) => total=560
    assert c.total() == 560.0


def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("expensive", 800)
    # coupon SAVE20 gives 20% off -> 640, shipping 60 -> 700 (non-member)
    assert c.total(coupon="SAVE20") == 700.0
    # member gets half shipping -> 30 -> total 670
    assert c.total(member=True, coupon="SAVE20") == 670.0


def test_cart_total_rounding_and_zero_case():
    c = Cart()
    # Empty cart: no shipping
    assert c.total() == 0.0
    # Rounding example: price 99.99 with 10% coupon -> discounted=89.991, shipping 60 => total=149.991 round 150.0
    c.add_item("item", 99.99)
    assert c.total(coupon="SAVE10") == 150.0


def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("test", 100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
