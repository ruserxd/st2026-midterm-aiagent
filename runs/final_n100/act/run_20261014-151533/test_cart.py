import pytest
from cart import Cart, parse_coupon, shipping_fee

def test_empty_cart_total():
    c = Cart()
    assert c.total() == 0.00

# Subtotal and total without coupon

def test_subtotal_and_total_no_coupon():
    c = Cart()
    c.add_item("apple", 1.5, 2)   # 3.0
    c.add_item("banana", 0.75, 4)  # 3.0
    assert c.subtotal() == 6.0
    expected_total = round(6.0 + shipping_fee(6.0), 2)
    assert c.total() == expected_total

# Coupon application and rounding

def test_coupon_and_rounding():
    c = Cart()
    c.add_item("item", 10.00, 1)
    # assume parse_coupon returns percent value
    coupon_percent = parse_coupon("SAVE10")
    assert coupon_percent == 10
    discounted = round(10.0 * (1 - coupon_percent/100), 2)
    expected_total = round(discounted + shipping_fee(discounted), 2)
    assert c.total(coupon="SAVE10") == expected_total

# Invalid coupon raises ValueError

def test_invalid_coupon():
    c = Cart()
    c.add_item("item", 5.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
