import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_edge_cases():
    # zero percent discount
    assert apply_discount(100, 0) == 100.0
    # full discount
    assert apply_discount(50, 100) == 0.0


def test_apply_discount_rounding():
    # price with many decimals should be rounded to two decimals
    assert apply_discount(99.995, 10) == 90.0   # 99.995 * 0.9 = 89.9955 -> round 90.0


def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-1, 20)
    with pytest.raises(ValueError):
        apply_discount(100, -10)
    with pytest.raises(ValueError):
        apply_discount(100, 110)

# ---------- bulk_discount_percent ----------------------------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15


def test_bulk_discount_percent_errors():
    for bad in [0, -5, 3.2, "a"]:
        with pytest.raises(ValueError):
            bulk_discount_percent(bad)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe5") == 5


def test_parse_coupon_invalid():
    invalids = ["", "SAVEX", "SAVE51", "NOTC", "SAVE0", "SAVE-5"]
    for code in invalids:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee_non_member():
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0


def test_shipping_fee_member():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart class ----------------------------------------

def test_cart_basic_operations():
    cart = Cart()
    assert list(cart.items()) == []
    cart.add_item("apple", 2.0, quantity=3)
    cart.add_item("banana", 1.5)
    assert len(list(cart.items())) == 2
    # check internal representation via items()
    for name, unit_price, qty in cart.items():
        if name == "apple":
            assert unit_price == 2.0 and qty == 3
        elif name == "banana":
            assert unit_price == 1.5 and qty == 1


def test_cart_subtotal_and_total_no_discount():
    cart = Cart()
    cart.add_item("item", 100, quantity=2)
    assert cart.subtotal() == 200
    assert cart.total() == 200 + shipping_fee(200)   # default member=False


def test_cart_apply_member_and_coupon():
    cart = Cart()
    cart.add_item("item", 1000)
    # subtotal triggers free shipping
    assert cart.subtotal() == 1000
    # no discount, but member status halves fee (still zero)
    assert cart.total(member=True) == 1000
    # apply coupon 20% via parse_coupon
    total_with_coupon = cart.total(coupon=parse_coupon("SAVE20"))
    # subtotal 1000 minus 20% = 800, shipping free -> 800
    assert total_with_coupon == 800.0

# Test bulk discount integration in total

def test_cart_bulk_discount_in_total():
    cart = Cart()
    cart.add_item("widget", 50, quantity=12)   # bulk discount 5%
    expected_subtotal = 50 * 12
    discounted_price = apply_discount(expected_subtotal, bulk_discount_percent(12))
    expected_total = discounted_price + shipping_fee(discounted_price)
    assert cart.total() == pytest.approx(expected_total, rel=1e-9)

# Ensure removal updates correctly

def test_cart_removal():
    cart = Cart()
    cart.add_item("item", 10, quantity=5)
    cart.remove_item("item", quantity=3)
    # remaining quantity 2
    items = list(cart.items())
    assert len(items) == 1 and items[0][2] == 2
    cart.remove_item("item", quantity=2)
    assert list(cart.items()) == []
