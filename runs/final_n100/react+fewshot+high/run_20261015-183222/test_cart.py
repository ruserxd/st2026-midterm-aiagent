import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Test for applying discount percentage to a price.

def test_apply_discount():
    # Simple cases with expected mathematical outcome.
    assert apply_discount(100.0, 20) == pytest.approx(80.0)
    # Zero percent: price unchanged
    assert apply_discount(50.0, 0) == pytest.approx(50.0)
    # Full discount: result zero
    assert apply_discount(30.0, 100) == pytest.approx(0.0)

# Test bulk discount calculation – only general constraints are checked.

def test_bulk_discount_percent():
    for qty in [1, 5, 10, 20]:
        disc = bulk_discount_percent(qty)
        assert isinstance(disc, (int, float))
        assert 0 <= disc <= 100

# Test coupon parsing – assumes a simple “CODENN” format.

def test_parse_coupon():
    code = "SAVE15"
    coupon = parse_coupon(code)
    assert isinstance(coupon, dict)
    assert coupon.get("code") == code
    assert coupon.get("discount") == 15

    # Invalid format should raise ValueError.
    with pytest.raises(ValueError):
        parse_coupon("INVALID")

# Test shipping fee calculation for members and non‑members.

def test_shipping_fee():
    # Non‑member: fee >0 for a small subtotal.
    assert shipping_fee(30.0) > 0
    # Member gets free shipping regardless of order amount.
    assert shipping_fee(10.0, member=True) == 0.0
    assert shipping_fee(200.0, member=True) == 0.0

# Test cart item addition and removal logic.

def test_cart_add_and_remove():
    cart = Cart()
    cart.add_item("apple", 1.0, quantity=2)
    cart.add_item("banana", 0.5, quantity=3)
    items = cart.items()
    assert items["apple"] == 2
    assert items["banana"] == 3

    # Remove part of a quantity.
    cart.remove_item("banana", quantity=1)
    assert cart.items()["banana"] == 2

    # Removing all of an item by omitting quantity or exceeding existing.
    cart.remove_item("apple")
    assert "apple" not in cart.items()

# Test subtotal and total calculation, including shipping and coupon discounts.

def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item("item1", 10.0, quantity=2)   # subtotal 20
    cart.add_item("item2", 5.0, quantity=1)    # subtotal 25

    assert cart.subtotal() == pytest.approx(25.0)

    expected_total = 25.0 + shipping_fee(25.0)
    assert cart.total(member=False) == pytest.approx(expected_total)

    # Member has free shipping.
    assert cart.total(member=True) == pytest.approx(25.0)

    coupon = {"code": "DIS10", "discount": 10}
    total_with_coupon = cart.total(member=False, coupon=coupon)
    expected_total_discounted = expected_total - (expected_total * (coupon["discount"] / 100))
    assert total_with_coupon == pytest.approx(expected_total_discounted)
