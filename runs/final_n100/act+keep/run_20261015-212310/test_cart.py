import pytest
import cart

# Helper for rounding in tests
from math import isclose

def approx_equal(a, b, eps=1e-9):
    return isclose(a, b, abs_tol=eps)

# --- apply_discount ---------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0


def test_apply_discount_rounding():
    # 33% of 1 is 0.33 -> 0.67 after discount
    assert cart.apply_discount(1, 33) == round(1 * (1 - 33/100), 2)


def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 101)

# --- bulk_discount_percent ---------------------------------------------

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(200) == 15


def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)  # non-integer

# --- parse_coupon ------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon(" SAVE30") == 30


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAve")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")
    with pytest.raises(ValueError):
        cart.parse_coupon("BAD10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # above allowed max

# --- shipping_fee ------------------------------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500, member=False) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# --- Cart class --------------------------------------------------------

def test_cart_add_and_items_and_subtotal():
    c = cart.Cart()
    assert c.items() == []
    c.add_item("apple", 2.5, quantity=3)
    assert c.items() == [("apple", 2.5, 3)]
    # subtotal: 3*2.5
    assert c.subtotal() == 7.5
    c.add_item("banana", 1.0)  # default qty 1
    assert set(c.items()) == {("apple", 2.5, 3), ("banana", 1.0, 1)}
    assert approx_equal(c.subtotal(), 7.5 + 1.0)


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("apple", 2.0, quantity=5)
    c.remove_item("apple", quantity=3)
    assert c.items() == [("apple", 2.0, 2)]
    # removing more than exists should remove the item
    c.remove_item("apple", quantity=5)
    assert c.items() == []


def test_cart_total_no_coupon_member_false():
    c = cart.Cart()
    c.add_item("item", 10, quantity=2)  # subtotal 20
    total = c.total(member=False)
    # no coupon => shipping fee 60 (non-member), result 80
    assert approx_equal(total, 80.0)


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 50, quantity=1)  # subtotal 50
    total = c.total(member=True, coupon="SAVE20")
    # discount: 20% of 50 => 40. shipping fee for member on discounted subtotal 40 -> 30
    # total 70
    assert approx_equal(total, 70.0)


def test_cart_total_with_bulk_discount_and_free_shipping():
    c = cart.Cart()
    c.add_item("expensive", 200, quantity=10)  # subtotal 2000
    total = c.total(member=False)
    # no coupon; shipping free because subtotal >=1000 -> 0
    assert approx_equal(total, 2000.0)


def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")

# --- Integration: verify rounding to two decimals ----------------------

def test_cart_total_rounding():
    c = cart.Cart()
    # price that leads to non-terminating decimal after discount
    c.add_item("odd", 1.33, quantity=3)  # subtotal 3.99
    total = c.total(coupon="SAVE10")  # 10% off => 3.591 -> round to 3.59 shipping fee 60 non-member
    assert approx_equal(total, 63.59)
