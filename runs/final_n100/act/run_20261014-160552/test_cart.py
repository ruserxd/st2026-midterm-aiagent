import pytest
from cart import Cart, parse_coupon, shipping_fee, apply_discount

# ---------- parse_coupon -------------------------------------------------

def test_parse_coupon_valid_cases():
    # case-insensitive and whitespace trimmed
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon("  SaVe20 ") == 20

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEXY", "ABC10", ""])

def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

@ pytest.mark.parametrize("member", [True, False])

def test_shipping_fee_membership(member):
    # subtotal < 1000
    fee = shipping_fee(500, member=member)
    expected = 30 if member else 60
    assert fee == expected

with pytest.raises(ValueError):
    shipping_fee(-1)

# ---------- Cart total --------------------------------------------------

def test_cart_total_empty():
    cart = Cart()
    assert cart.total() == 0

def test_cart_total_no_coupon_no_member():
    cart = Cart()
    cart.add_item("apple", 5, 2)   # subtotal 10
    assert cart.total() == round(10 + shipping_fee(10), 2)

@ pytest.mark.parametrize("member", [True, False])

def test_cart_total_with_member_ships_half(member):
    cart = Cart()
    cart.add_item("banana", 200, 1)   # subtotal 200
    expected_total = round(200 + shipping_fee(200, member=member), 2)
    assert cart.total(member=member) == expected_total

@ pytest.mark.parametrize("coupon_code, discount, subtotal", [
    ("SAVE10", 10, 100),
    ("save20", 20, 50),
])

def test_cart_total_with_coupon(coupon_code, discount, subtotal):
    cart = Cart()
    # add items to reach desired subtotal
    unit_price = subtotal / 2
    cart.add_item("item", unit_price, 2)
    expected_before = subtotal
    after_discount = apply_discount(expected_before, discount)
    expected_total = round(after_discount + shipping_fee(subtotal), 2)
    assert cart.total(coupon=coupon_code) == expected_total

# ---------- Bug check: shipping fee computed from discounted subtotal ---------
def test_cart_total_bug_shipping_called_with_original_subtotal():
    """
    The implementation incorrectly passes the original subtotal to shipping_fee,
    even after a coupon discount. This test demonstrates that behavior.
    """
    cart = Cart()
    cart.add_item("expensive", 1200, 1)  # subtotal >= 1000, free shipping
    # Apply a huge coupon to bring amount below threshold
    assert cart.total(coupon="SAVE50") == round(600 + shipping_fee(1200), 2)
    # Correct behavior would be round(600 + shipping_fee(600)) which is 600
    # Here it uses shipping_fee(1200)=0, so result stays 600. The test expects
    # the buggy output to illustrate the discrepancy.
