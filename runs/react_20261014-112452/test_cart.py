import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.99, 33, round(99.99 * 0.67, 2)),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, abs=1e-2)

# error conditions
@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("  Save50 ", 50),
        ("SAVE1", 1),
        ("SAVE0", None),  # invalid
    ],
)
def test_parse_coupon_valid(code, expected):
    if expected is not None:
        assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "NOPE10", "SAVE51", "saver10", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart subtotal and total ----------

def test_cart_subtotal_and_total_basic():
    c = Cart()
    # add 5 items each $10, no bulk discount
    for i in range(5):
        c.add_item(f"item{i}", 10)
    assert c.subtotal() == pytest.approx(50.0)
    # total without coupon or membership
    assert c.total() == pytest.approx(110.0)  # 50 + 60 shipping

def test_cart_bulk_discount_and_shipment():
    c = Cart()
    c.add_item("bulk", 20, quantity=120)  # bulk discount 15%
    # subtotal: 20*120*0.85 = 2040
    assert c.subtotal() == pytest.approx(2040.0)
    # shipping free because >=1000 before coupon
    assert c.total(member=True) == pytest.approx(2040.0)

def test_cart_coupon_and_shipping():
    c = Cart()
    c.add_item("product", 30, quantity=5)  # no bulk discount: subtotal 150
    # apply coupon SAVE10 -> 135 then shipping 60 => total 195
    assert c.total(coupon="SAVE10") == pytest.approx(195.0)

def test_cart_empty():
    c = Cart()
    assert c.subtotal() == 0
    assert c.total() == 0

# ---------- remove_item functionality ----------

def test_remove_item():
    c = Cart()
    c.add_item("widget", 5, quantity=3)
    c.remove_item("widget")  # default quantity 1
    assert any(item["name"] == "widget" and item["quantity"] == 2 for item in c.items())
    c.remove_item("widget", quantity=2)
    # widget should be removed entirely
    assert all(item["name"] != "widget" for item in c.items())
