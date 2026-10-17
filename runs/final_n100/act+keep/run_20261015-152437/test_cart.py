import pytest
from cart import Cart, parse_coupon, shipping_fee

# ---------------------
# Coupon parsing tests
# ---------------------

def test_parse_valid_coupons():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe5") == 5

@ pytest.mark.parametrize("code", ["save0", "save51", "foo10", ""])

def test_parse_invalid_coupons(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------------------
# Shipping fee tests
# ---------------------

def test_shipping_fee_regular_and_member():
    # subtotal >= 1000, free for everyone
    assert shipping_fee(1200) == 0
    assert shipping_fee(1200, member=True) == 0

    # subtotal < 1000: non-member 60, member 30
    assert shipping_fee(999) == 60
    assert shipping_fee(999, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10.5])

def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------------------
# Cart functionality tests
# ---------------------

def test_empty_cart_total():
    cart = Cart()
    assert cart.total() == 0
    assert cart.subtotal() == 0


def test_add_and_subtotal():
    cart = Cart()
    cart.add_item("apple", 200, quantity=3)
    cart.add_item("banana", 150, quantity=2)
    # subtotal: 3*200 + 2*150 = 600 + 300 = 900
    assert cart.subtotal() == 900


def test_remove_item():
    cart = Cart()
    cart.add_item("apple", 100, quantity=5)
    cart.remove_item("apple", quantity=2)
    # remaining: 3 apples
    assert cart.subtotal() == 300

    # removing more than existing reduces to zero (implementation may raise but spec doesn't cover; test normal behavior)
    cart.remove_item("apple", quantity=5)  # should leave 0
    assert cart.subtotal() == 0


def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("widget", 800, quantity=1)   # subtotal 800
    # No coupon: total = 800 + shipping(60) = 860
    assert cart.total() == 860

    # With valid coupon SAVE10: 10% off -> 720 + shipping(60?) wait: after coupon amount 720, shipping fee applies to that amount. 720 < 1000 => 60.
    assert cart.total(coupon="SAVE10") == round(720+60,2)

    # With coupon that brings below free threshold? Example subtotal 1100 with 50% off -> 550 < 1000 so shipping 60.
    cart = Cart()
    cart.add_item("expensive", 1100, quantity=1)
    assert cart.total(coupon="SAVE50") == round(550+60,2)


def test_total_member_shipping():
    cart = Cart()
    cart.add_item("item", 900, quantity=1)  # subtotal 900
    assert cart.total(member=True) == 960  # shipping 30

    # member with coupon SAVE50 -> 450 + shipping 30 = 480
    assert cart.total(member=True, coupon="SAVE50") == round(450+30,2)


def test_invalid_coupon_in_total():
    cart = Cart()
    cart.add_item("thing", 200, quantity=1)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

# ---------------------
# Edge cases
# ---------------------

def test_rounding_of_total():
    cart = Cart()
    # Add item price that leads to fraction when coupon applied
    cart.add_item("precise", 333, quantity=3)  # subtotal 999
    # Apply SAVE10 => 899.1 ; shipping 60 => 959.1 -> round 959.1
    assert cart.total(coupon="SAVE10") == 959.1

# Note: The specification states rounding to 2 decimals, but the implementation may or may not round correctly.
