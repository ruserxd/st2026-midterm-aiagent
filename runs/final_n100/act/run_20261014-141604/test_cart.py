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

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize(
    "qty",
    [0, -5, 2.5],
)
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(int(qty))

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("  SaVe5 ") == 5

@pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVE0", "SAVE51", "ABCD10", " save-5 ", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code) if code is not None else None

# ---------- shipping_fee ----------

def test_shipping_fee_basic():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(50, member=True) == 30

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class basics ----------

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 100, quantity=3)
    c.add_item("banana", 50, quantity=2)
    assert c.items()["apple"] == (100, 3)
    assert c.items()["banana"] == (50, 2)
    # subtotal: 3*100 + 2*50 = 400
    assert c.subtotal() == 400
    # remove one apple
    c.remove_item("apple", quantity=1)
    assert c.items()["apple"] == (100, 2)
    # remove all bananas
    c.remove_item("banana")
    assert "banana" not in c.items()
    # final subtotal: 2*100 = 200
    assert c.subtotal() == 200


def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("widget", 500, quantity=3)  # subtotal 1500
    # coupon SAVE10 -> 10% off subtotal -> 1350
    total = c.total(coupon="SAVE10")
    assert total == round(1350 + shipping_fee(1350), 2)

    # member discount on shipping: same 15% off before shipping, shipping half
    total_member = c.total(member=True, coupon="SAVE10")
    expected = round((1500 * 0.90) + shipping_fee(1350, member=True), 2)
    assert total_member == expected

# ---------- Edge cases: empty cart shipping not applied ----------

def test_cart_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0
