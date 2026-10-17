import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE20 ") == 20

@pytest.mark.parametrize(
    "code",
    ["", "SAVE0", "SAVE51", "savelink", "1234", "SAVE-5", "SAVE50x"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

    # member discount
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

with pytest.raises(ValueError):
    shipping_fee(-1)

# ---------- Cart tests ----------

def test_cart_total_empty():
    c = Cart()
    # Empty cart should cost 0 and not charge shipping
    assert c.total() == 0


def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", 100, quantity=3)
    assert c.subtotal() == 300

    # adding more of the same item updates quantity and price
    c.add_item("apple", 100, quantity=2)
    assert c.items()["apple"] == (100, 5)
    assert c.subtotal() == 500


def test_cart_remove():
    c = Cart()
    c.add_item("banana", 200, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items()["banana"] == (200, 2)
    assert c.subtotal() == 400

    # removing more than exists should leave zero
    c.remove_item("banana", quantity=5)
    assert "banana" not in c.items()


def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("laptop", 1500)
    # subtotal before discount: 1500
    amount_after_discount = apply_discount(1500, parse_coupon("SAVE10"))
    # shipping after discount on subtotal (since coupon applied first in code)
    shipping = shipping_fee(amount_after_discount, member=True)
    expected_total = round(amount_after_discount + shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# Test that invalid coupon propagates error

def test_cart_invalid_coupon():
    c = Cart()
    c.add_item("pen", 50)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
