import cart
import pytest

# ---------- Helper functions for expected calculations ----------

def expected_apply_discount(price, percent):
    if price < 0:
        with pytest.raises(ValueError):
            return None
    if not (0 <= percent <= 100):
        with pytest.raises(ValueError):
            return None
    return round(price * (1 - percent / 100), 2)

# ---------- Tests for individual functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(10.00, 5) == 9.50
    # Edge cases
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)


def test_apply_discount_invalid_percent():
    for bad in [-1, 101]:
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.5)


def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("sAvE1") == 1


def test_parse_coupon_invalid():
    for bad in ["SAVEx", "save51", "ABC12", "SAVE-5", ""]:
        with pytest.raises(ValueError):
            cart.parse_coupon(bad)


def test_shipping_fee():
    # Non-member, non-free shipping
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    # Member gets half
    assert cart.shipping_fee(300, member=True) == 30
    assert cart.shipping_fee(10, member=True) == 30
    # Free shipping over threshold
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0


def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ---------- Tests for Cart class behaviour ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 2.0, quantity=5)
    assert c.items()["apple"] == 5
    # Adding more of same item updates quantity
    c.add_item("apple", 2.0, quantity=3)
    assert c.items()["apple"] == 8

    # Adding with different unit price should raise
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0, quantity=1)

    # Remove some items
    c.remove_item("apple", quantity=4)
    assert c.items()["apple"] == 4

    # Removing more than existing should remove the item
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()

    # Removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("banana")


def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 10 units => 5% bulk discount
    c.add_item("widget", 20.0, quantity=10)
    expected_line = 20.0 * 10 * 0.95
    assert c.subtotal() == round(expected_line, 2)

    # More items to trigger higher discount
    c.add_item("gadget", 5.0, quantity=55)  # 10% discount
    line_total = 5.0 * 55 * 0.90
    assert c.subtotal() == round(expected_line + line_total, 2)


def test_cart_total_without_coupon_or_membership():
    c = cart.Cart()
    c.add_item("item", 100.0, quantity=1)  # no bulk discount
    # subtotal 100, shipping fee 60 -> total 160
    assert c.total() == 160.00


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 2000.0, quantity=1)
    # subtotal 2000, coupon SAVE10 => 1800, shipping fee free because subtotal >=1000
    assert c.total(member=True, coupon="SAVE10") == 1800.00


def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 50.0)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
