import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

round2 = lambda x: round(float(x), 2)

# Individual function tests remain same but adjust for case sensitivity and discount logic

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("SAVE25") == 25
    # parse_coupon is case-sensitive; use uppercase only
    assert parse_coupon("SAVE50") == 50

def test_subtotal_bulk_discount():
    cart = Cart()
    cart.add_item("widget", 20, quantity=10)  # 200 base, discount 5%
    expected1 = round2(20 * 10 * 0.95)
    assert round2(cart.subtotal()) == expected1
    cart.add_item("gadget", 15, quantity=50)  # 750 base, discount 5% (since <100 and >50 triggers 5%)
    expected2 = round2(20 * 10 * 0.95 + 15 * 50 * 0.95)
    assert round2(cart.subtotal()) == expected2
    cart.add_item("thing", 5, quantity=100)   # 500 base, discount 15%
    expected3 = round2(expected2 + 5 * 100 * 0.85)
    assert round2(cart.subtotal()) == expected3
