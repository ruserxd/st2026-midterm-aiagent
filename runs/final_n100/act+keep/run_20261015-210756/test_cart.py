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

@ pytest.mark.parametrize(
    "price,percent,expected",
    [ (100, 0, 100.0), (50, 100, 0.0), (75.25, 10, 67.725), ],
)
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == round(expected, 2)

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize(
    "percent",
    [-5, 101, 200],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_bounds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save5") == 5
    assert parse_coupon(" SAVE20 ") == 20
    # case-insensitive and surrounding whitespace handled

@ pytest.mark.parametrize(
    "code",
    ["", "SAVE0", "SAVE51", "SAVEX", "DISCOUNT10", "12345", None],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    # free shipping threshold
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.5) == 0
    # non-member fee
    assert shipping_fee(999.99) == 60
    # member half fee
    assert shipping_fee(500, member=True) == 30
    # rounding irrelevant as integer values

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart subtotal & bulk discount integration ----------

def test_cart_subtotal_with_bulk_discount():
    cart = Cart()
    # 5 units, no bulk discount
    cart.add_item("widget", unit_price=10.0, quantity=5)
    assert cart.subtotal() == 50.0
    # add another item with bulk discount threshold
    cart.add_item("gadget", unit_price=20.0, quantity=12)  # 10% discount
    expected_gadget_total = 20.0 * 12 * (1 - 0.05)
    assert cart.subtotal() == round(50.0 + expected_gadget_total, 2)

# ---------- Cart total with coupon and shipping ----------

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("widget", unit_price=200.0, quantity=1)
    # subtotal: 200
    # apply coupon SAVE10 -> 180
    total = cart.total(coupon="SAVE10")
    assert total == round(180 + shipping_fee(180), 2)  # shipping 60 => 240

def test_cart_total_with_member_and_bulk_discount():
    cart = Cart()
    cart.add_item("bulkitem", unit_price=50.0, quantity=120)  # 15% discount
    subtotal = 50.0 * 120 * (1 - 0.15)
    total_no_coupon = round(subtotal + shipping_fee(subtotal), 2)
    assert cart.total(member=True) == total_no_coupon

# ---------- Cart empty behavior ----------

def test_empty_cart_total_and_shipping():
    cart = Cart()
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0

# ---------- add_item validation ----------

def test_add_item_same_name_different_price_raises():
    cart = Cart()
    cart.add_item("foo", unit_price=10, quantity=1)
    with pytest.raises(ValueError):
        cart.add_item("foo", unit_price=12, quantity=2)

# ---------- remove_item validation ----------

def test_remove_item_updates_and_removes():
    cart = Cart()
    cart.add_item("widget", unit_price=5.0, quantity=3)
    cart.remove_item("widget", quantity=1)
    assert cart.items()["widget"] == 2
    cart.remove_item("widget", quantity=2)  # should remove completely
    assert "widget" not in cart.items()

with pytest.raises(KeyError):
    cart = Cart()
    cart.remove_item("nonexistent")
