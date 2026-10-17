# test_cart.py

import re
import pytest

import cart


def test_apply_discount_valid_cases():
    # Basic functionality
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

    # Rounding to two decimals
    assert cart.apply_discount(99.999, 10) == round(99.999 * 0.9, 2)
    assert cart.apply_discount(123.456, 33.3333) == round(
        123.456 * (1 - 33.3333 / 100), 2
    )


def test_apply_discount_invalid_inputs():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 101)


def test_bulk_discount_percent_cases():
    # boundary values
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

    # Larger numbers
    assert cart.bulk_discount_percent(1010) == 15


def test_bulk_discount_invalid_inputs():
    for bad in [0, -1, 3.14, "ten", None]:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(bad)


def test_parse_coupon_valid_cases():
    valid_codes = ["SAVE10", "save50", "   SaVe25   ", "saVE1"]
    expected = [10, 50, 25, 1]
    for code, exp in zip(valid_codes, expected):
        assert cart.parse_coupon(code) == exp


def test_parse_coupon_invalid_cases():
    invalids = ["SAV5", "SAVE0", "SAVE51", "DISCOUNT10", "", "1234", "   ", "SAVE-5"]
    for code in invalids:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)


def test_shipping_fee_basic():
    # Non-member
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

    # Member
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(499.5, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0


def test_shipping_fee_invalid_inputs():
    for bad in [-1, -100, -0.01, None]:
        with pytest.raises(ValueError):
            cart.shipping_fee(bad)

@pytest.fixture
def sample_cart():
    """A helper that returns a fresh Cart instance."""
    return cart.Cart()


def test_cart_add_and_items(sample_cart):
    sample_cart.add_item("apple", 10, 3)
    sample_cart.add_item("banana", 5)

    # Default quantity is 1
    assert sample_cart.items() == {
        "apple": (10, 3),
        "banana": (5, 1),
    }

    # Adding more of the same item increments quantity
    sample_cart.add_item("apple", 10, 2)
    assert sample_cart.items()["apple"][1] == 5


def test_cart_remove_and_items(sample_cart):
    sample_cart.add_item("cherry", 20, 4)
    sample_cart.remove_item("cherry")
    # Default removal quantity is 1
    assert sample_cart.items()["cherry"][1] == 3

    sample_cart.remove_item("cherry", 2)
    assert sample_cart.items()["cherry"][1] == 1

    # Removing the last unit removes the item completely
    sample_cart.remove_item("cherry")
    assert "cherry" not in sample_cart.items()


def test_cart_subtotal(sample_cart):
    sample_cart.add_item("item1", 7.5, 4)   # 30.0
    sample_cart.add_item("item2", 3.333, 3)  # 9.999
    assert sample_cart.subtotal() == pytest.approx(39.999)


def test_cart_total_with_discounts_and_shipping(sample_cart):
    sample_cart.add_item("widget", 200, 60)   # subtotal 12000

    # bulk discount applies to each item individually; 60 units => 10% off
    discounted_unit = cart.apply_discount(200, cart.bulk_discount_percent(60))
    assert discounted_unit == cart.apply_discount(200, 10)

    # subtotal after discount
    expected_subtotal = discounted_unit * 60
    assert sample_cart.subtotal() == pytest.approx(expected_subtotal)

    # member shipping is free because subtotal >= 1000
    assert cart.shipping_fee(sample_cart.subtotal(), member=True) == 0

    total = sample_cart.total(member=True)
    assert total == pytest.approx(expected_subtotal)

    # Applying a coupon reduces the total
    # Coupon "SAVE20" => 20% off the subtotal
    coupon_discounted = cart.apply_discount(
        expected_subtotal, cart.parse_coupon("SAVE20")
    )
    assert sample_cart.total(member=True, coupon="SAVE20") == pytest.approx(coupon_discounted)


def test_cart_total_invalid_coupon(sample_cart):
    sample_cart.add_item("test", 50)
    with pytest.raises(ValueError):
        sample_cart.total(coupon="INVALID")


def test_cart_total_member_flag_and_shipping_behavior():
    """Test that shipping fee is correctly computed when member flag changes."""
    s = cart.Cart()
    s.add_item("a", 200, 5)          # subtotal 1000
    assert s.total(member=False) == pytest.approx(1000 + 60)   # non‑member pays full fee
    assert s.total(member=True) == pytest.approx(1000)         # member gets free shipping


def test_cart_total_with_zero_subtotal(sample_cart):
    """If no items, total should be just the shipping fee (which is 60 for non‑members)."""
    assert sample_cart.subtotal() == 0
    assert sample_cart.total(member=False) == 60
    assert sample_cart.total(member=True) == 30
