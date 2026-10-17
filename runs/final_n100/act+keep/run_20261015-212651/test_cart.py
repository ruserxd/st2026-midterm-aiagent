import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Discount functions ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 5), (50, -1), (50, 101)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Bulk discount percentages ----------

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 5),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Coupon parsing ----------

@pytest.mark.parametrize(
    "code,result",
    [
        ("SAVE10", 10),
        ("SAVE5", 5),
    ],
)
def test_parse_coupon_valid(code, result):
    assert parse_coupon(code) == result

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",
        "SAVEXX",
        "DISCOUNT10",
        "save51",
        "",
        None,
        " SAVE10 ",  # trailing spaces not allowed
        "sAvE50",      # mixed case not allowed
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Shipping fee ----------

@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, result):
    assert shipping_fee(subtotal, member=member) == result

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart behavior ----------

def test_empty_cart_totals():
    cart = Cart()
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0


def test_add_and_subtotal():
    cart = Cart()
    cart.add_item("widget", unit_price=10, quantity=5)
    assert cart.subtotal() == 50.0
    cart.add_item("widget", unit_price=10, quantity=6)  # total qty=11 - bulk discount 5%
    expected = round(10 * 11 * 0.95, 2)
    assert cart.subtotal() == pytest.approx(expected, rel=1e-9)


def test_remove_item():
    cart = Cart()
    cart.add_item("gadget", unit_price=20, quantity=3)
    cart.remove_item("gadget", quantity=2)
    assert cart.items() == {"gadget": 1}
    cart.remove_item("gadget")
    # Implementation keeps key with value 0
    assert cart.items() == {"gadget": 0}

    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")


def test_add_same_name_different_price():
    cart = Cart()
    cart.add_item("item", unit_price=5, quantity=2)
    with pytest.raises(ValueError):
        cart.add_item("item", unit_price=6, quantity=1)


def test_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("book", unit_price=30, quantity=4)  # subtotal 120
    total = cart.total(coupon="SAVE10")
    expected = round(108 + 60, 2)
    assert total == pytest.approx(expected, rel=1e-9)
    member_total = cart.total(member=True, coupon="SAVE10")
    expected_member = round(108 + 30, 2)
    assert member_total == pytest.approx(expected_member, rel=1e-9)


def test_total_invalid_coupon():
    cart = Cart()
    cart.add_item("pen", unit_price=5, quantity=2)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

# Verify rounding behavior for subtotal and total

def test_rounding_behavior():
    cart = Cart()
    cart.add_item("toy", unit_price=1.3333, quantity=3)
    assert cart.subtotal() == 4.0
    cart.add_item("board", unit_price=2.2222, quantity=4)
    expected = round(4.0 + 8.8888, 2)
    assert cart.subtotal() == pytest.approx(expected, rel=1e-9)
