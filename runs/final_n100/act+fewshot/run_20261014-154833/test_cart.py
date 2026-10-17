import pytest
import cart

# Helper function for rounding check in apply_discount

def test_apply_discount_valid_cases():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    # rounding check
    assert cart.apply_discount(33.333, 10) == round(33.333 * (1 - 0.10), 2)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)


def test_apply_discount_invalid_percent():
    for bad in [-1, 101]:
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)


def test_bulk_discount_percent_cases():
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
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)


def test_parse_coupon_valid():
    for code in ["SAVE10", "save20", " SAVE30 ", "SaVe40"]:
        assert 1 <= int(code.strip().upper()[4:]) <= 50
        # parse_coupon should return that integer
        assert cart.parse_coupon(code) == int(code.strip().upper()[4:])


def test_parse_coupon_invalid():
    for code in ["SAVEX", "save0", "save51", " abc123 ", "SAVE-10", ""]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)


def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # member discount
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0


def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Tests for Cart class

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == []
    c.add_item("apple", 1.0, quantity=3)
    assert c.items() == [("apple", 1.0, 3)]
    c.add_item("banana", 0.5)
    assert c.items() == [("apple", 1.0, 3), ("banana", 0.5, 1)]


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("apple", 1.0, quantity=5)
    c.remove_item("apple", quantity=2)
    assert c.items() == [("apple", 1.0, 3)]
    # remove more than present should raise
    with pytest.raises(ValueError):
        c.remove_item("apple", quantity=4)
    # removing nonexistent item raises
    with pytest.raises(KeyError):
        c.remove_item("orange")


def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("a", 10.0, 2)   # 20
    c.add_item("b", 5.0, 3)    # 15
    assert c.subtotal() == 35.0


def test_cart_total_no_discount():
    c = cart.Cart()
    c.add_item("a", 100.0)
    # subtotal 100, shipping 60 -> total 160
    assert c.total() == 160.0
    # member discount on shipping only
    assert c.total(member=True) == 130.0


def test_cart_total_with_bulk_discount_and_coupon():
    c = cart.Cart()
    c.add_item("widget", 10.0, quantity=120)  # bulk 15% off unit price -> 8.5 each
    # subtotal after bulk discount: 8.5 * 120 = 1020
    assert c.subtotal() == 1020.0
    # shipping free because subtotal >=1000
    assert c.total() == 1020.0
    # apply coupon SAVE10 (10%) on the total before shipping? Spec unclear; assume applies to subtotal
    assert c.total(coupon="SAVE10") == round(1020 * 0.90, 2)


def test_cart_total_with_coupon_and_member_shipping():
    c = cart.Cart()
    c.add_item("a", 200.0)   # subtotal 200
    total_before_ship = 200.0
    shipping_fee = 60
    total_no_coupon = 260.0
    # with coupon SAVE5 -> 5% off subtotal: 190
    assert c.total(coupon="SAVE5") == round(200 * 0.95 + shipping_fee, 2)
    # with member discount on shipping
    assert c.total(member=True, coupon="SAVE5") == round(200 * 0.95 + 30, 2)
