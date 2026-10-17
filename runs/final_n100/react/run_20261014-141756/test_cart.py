import math
import pytest
import cart

# apply_discount tests

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0


def test_apply_discount_invalid():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    for bad in (-5, 101):
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)

# bulk_discount_percent tests

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_invalid():
    for bad in (0, -1):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(bad)

# parse_coupon tests

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE5 ") == 5


def test_parse_coupon_invalid():
    for code in ["", "SAVExx", "saver10", "SAVE51", "NOPE"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# shipping_fee tests

def test_shipping_fee_values():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    assert cart.shipping_fee(500, member=True) == 30


def test_shipping_fee_invalid():
    for bad in (-1, -50):
        with pytest.raises(ValueError):
            cart.shipping_fee(bad)

# Cart class tests

def test_cart_operations():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    c.add_item("apple", 100, quantity=2)
    assert c.items()["apple"] == (100, 2)
    assert c.subtotal() == 200
    c.add_item("apple", 100, quantity=3)
    assert c.items()["apple"] == (100, 5)
    assert c.subtotal() == 500
    c.remove_item("apple", quantity=2)
    assert c.items()["apple"] == (100, 3)
    assert c.subtotal() == 300
    c.remove_item("apple")
    assert "apple" not in c.items()


def test_cart_total_discounts_and_coupons():
    c = cart.Cart()
    c.add_item("widget", 100, quantity=10)  # bulk discount 5%
    subtotal = 1000
    total_no_discount = cart.apply_discount(subtotal, 5) + cart.shipping_fee(subtotal)
    assert c.total(member=False) == total_no_discount
    total_member = cart.apply_discount(subtotal, 5) + (cart.shipping_fee(subtotal)/2)
    assert c.total(member=True) == total_member
    c.add_item("extra", 50, quantity=1)
    subtotal_with_extra = subtotal + 50
    discounted = cart.apply_discount(subtotal_with_extra, 5)
    coupon_pct = cart.parse_coupon("SAVE20")
    expected_total = discounted - (discounted * coupon_pct / 100) + cart.shipping_fee(subtotal_with_extra)
    assert math.isclose(c.total(member=False, coupon="SAVE20"), expected_total, rel_tol=1e-9)

# Invalid add/remove

def test_cart_invalid_add_and_remove():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -10, 1)
    with pytest.raises(ValueError):
        c.add_item("zero_qty", 10, 0)
    c.add_item("test", 10, quantity=2)
    with pytest.raises(ValueError):
        c.remove_item("test", quantity=5)

# Empty cart total

def test_total_empty_cart():
    assert cart.Cart().total() == 0

# Invalid coupon in total

def test_invalid_coupon_in_total():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
