import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent,expected", [
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_extremes(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_below():
    assert bulk_discount_percent(9) == 0

def test_bulk_discount_mid_values():
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

def test_bulk_discount_exact_edges():
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 0
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -5, 1.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["save0", "save51", "foo10", "SA VE10", "SAVEXX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_non_member():
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

def test_shipping_fee_member():
    assert shipping_fee(999, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", unit_price=50, quantity=2)
    c.add_item("banana", unit_price=30)
    assert c.items() == {"apple": (50, 2), "banana": (30, 1)}
    # subtotal: 2*50 + 1*30 = 130
    assert c.subtotal() == 130

    c.remove_item("apple", quantity=1)
    assert c.items()["apple"] == (50, 1)
    assert c.subtotal() == 80

    # remove more than present -> should reduce to zero but not negative
    c.remove_item("banana")
    assert "banana" not in c.items()
    assert c.subtotal() == 50


def test_cart_total_no_coupon_non_member():
    c = Cart()
    c.add_item("item", unit_price=200, quantity=3)  # subtotal 600
    # no coupon -> 600 + shipping 60 = 660
    assert c.total() == 660.0


def test_cart_total_with_coupon():
    c = Cart()
    c.add_item("item", unit_price=200, quantity=5)  # subtotal 1000
    # coupon SAVE10 reduces to 900 -> shipping free (subtotal >= 1000? after discount it's 900 < 1000)
    # shipping fee is 60 because 900 < 1000, but member? no
    assert c.total(coupon="SAVE10") == 960.0  # 900 + 60 = 960


def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("item", unit_price=50)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")


def test_cart_member_shipping_discount():
    c = Cart()
    c.add_item("item", unit_price=200, quantity=1)  # subtotal 200
    assert c.total(member=True) == 260.0  # 200 + shipping 30

# Edge: empty cart no shipping

def test_cart_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0.0
