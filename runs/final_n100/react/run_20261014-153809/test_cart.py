import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Utility tests for standalone functions ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100.0, 0.2, 80.0),
        (50.0, 0.05, 47.5),
    ],
)
def test_apply_discount(price, percent, expected):
    """apply_discount should reduce price by the given percentage."""
    assert apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0.0),   # <5: no discount
        (4, 0.0),   # edge case
        (5, 0.05),  # >=5 and <=9: 5%
        (10, 0.10), # >=10 and <=19: 10%
        (20, 0.15), # >=20: 15%
    ],
)
def test_bulk_discount_percent(quantity, expected):
    """Bulk discount percent based on quantity."""
    assert bulk_discount_percent(quantity) == pytest.approx(expected)

@pytest.mark.parametrize("code", ["SAVE10", "FREESHIP", "NEWCUSTOMER20"])
def test_parse_coupon_valid(code):
    result = parse_coupon(code)
    assert isinstance(result, dict)
    # keys must be percent_off and free_shipping
    assert set(result.keys()) == {"percent_off", "free_shipping"}
    # percent_off should be between 0 and 1 inclusive
    assert 0.0 <= result["percent_off"] <= 1.0

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (80.0, False, 5.0),   # subtotal < 100: $5 fee
        (120.0, False, 10.0), # subtotal >= 100: $10 fee
        (50.0, True, 0.0),    # member free shipping
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member=member) == pytest.approx(expected)

# ---------- Cart class tests ----------

@pytest.fixture
def cart():
    return Cart()

# Adding items updates item list and subtotal correctly.
def test_cart_add_and_subtotal(cart):
    cart.add_item("Apple", 1.0, quantity=3)
    cart.add_item("Banana", 0.5, quantity=6)
    assert len(cart.items()) == 2
    # Subtotal: 3*1 + 6*0.5 = 6
    assert cart.subtotal() == pytest.approx(6.0)

# Removing items reduces quantity and removes item when zero.
def test_cart_remove_and_subtotal(cart):
    cart.add_item("Orange", 2.0, quantity=4)
    cart.remove_item("Orange", quantity=2)  # remaining qty = 2
    assert cart.subtotal() == pytest.approx(4.0)
    cart.remove_item("Orange", quantity=2)  # item should be removed completely
    assert len(cart.items()) == 0
    assert cart.subtotal() == pytest.approx(0.0)

# Total calculation with member discount, shipping, and coupon.
def test_cart_total_with_discounts_and_shipping(cart):
    cart.add_item("T-Shirt", 20.0, quantity=3)  # subtotal = 60
    # No discounts or coupons
    total_no_discount = cart.total(member=False, coupon=None)
    assert total_no_discount == pytest.approx(60 + 5)  # $5 shipping fee

    # Member discount: 20% off items and free shipping
    total_member = cart.total(member=True, coupon=None)
    assert total_member == pytest.approx(60 * 0.8)

    # Coupon 'SAVE10' gives an additional 10% off after member discount
    total_coupon = cart.total(member=True, coupon="SAVE10")
    discounted_items = 60 * 0.8 * (1 - 0.1)  # 20% member + 10% coupon
    assert total_coupon == pytest.approx(discounted_items)

# Invalid coupon should raise ValueError.
def test_cart_total_invalid_coupon(cart):
    cart.add_item("Shoes", 50.0, quantity=1)
    with pytest.raises(ValueError):
        cart.total(member=False, coupon="INVALIDCODE")
