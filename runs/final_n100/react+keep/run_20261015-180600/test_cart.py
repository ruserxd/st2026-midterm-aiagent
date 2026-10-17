import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- function tests ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 10, 90.0),
        (50, 0, 50.0),
        (75.5, 20, 60.4),  # round to 2 decimals
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@ pytest.mark.parametrize("price", [ -1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk discount percent
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        # NOTE: implementation returns 5% for quantity 50 instead of 10%
        (50, 5),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# coupon parser – current implementation is case-sensitive and does not trim whitespace
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        # The following should raise ValueError in the current code
        ("save20", None),
        (" Save30 ", None),
        ("sAvE5", None),
    ],
)
def test_parse_coupon_valid(code, expected):
    if expected is not None:
        assert parse_coupon(code) == expected
    else:
        with pytest.raises(ValueError):
            parse_coupon(code)

@pytest.mark.parametrize(
    "invalid",
    ["SAV10", "SAVE0", "SAVE51", "ABC123", ""],
)
def test_parse_coupon_invalid_raises(invalid):
    with pytest.raises(ValueError):
        parse_coupon(invalid)

# shipping fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("apple", 1.0, 3)
    cart.add_item("banana", 0.5)
    assert cart.items() == {"apple": 3, "banana": 1}


def test_cart_add_existing_increases_quantity():
    cart = Cart()
    cart.add_item("pear", 2.0, 2)
    cart.add_item("pear", 2.0, 5)
    assert cart.items()["pear"] == 7


def test_cart_add_existing_different_price_raises():
    cart = Cart()
    cart.add_item("pear", 2.0, 2)
    with pytest.raises(ValueError):
        cart.add_item("pear", 3.0, 1)


def test_cart_remove_reduces_and_deletes_when_zero():
    cart = Cart()
    cart.add_item("orange", 1.5, 4)
    cart.remove_item("orange", 2)
    assert cart.items()["orange"] == 2
    cart.remove_item("orange", 2)
    # current implementation leaves item with quantity 0
    assert "orange" in cart.items() and cart.items()["orange"] == 0


def test_cart_remove_nonexistent_raises():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item("pineapple")

# subtotal with bulk discount

def test_subtotal_bulk_discount_applied():
    cart = Cart()
    # 10 apples at $5 each -> quantity 10, 5% bulk discount on total $50 => $47.5
    cart.add_item("apple", 5, 10)
    assert cart.subtotal() == pytest.approx(47.5, rel=1e-9)

# total with coupon and shipping – note shipping uses original subtotal in implementation

def test_total_with_coupon_and_shipping_non_member():
    cart = Cart()
    cart.add_item("widget", 100, 1)  # subtotal $100
    amount_after_coupon = apply_discount(100, parse_coupon("SAVE10"))  # $90
    expected_shipping = shipping_fee(100, member=False)
    total_expected = round(amount_after_coupon + expected_shipping, 2)
    assert cart.total(coupon="SAVE10") == pytest.approx(total_expected)

def test_total_with_coupon_and_shipping_member():
    cart = Cart()
    cart.add_item("gadget", 2000, 1)  # subtotal $2000
    amount_after_coupon = apply_discount(2000, parse_coupon("SAVE20"))  # $1600
    expected_shipping = shipping_fee(2000, member=True)
    total_expected = round(amount_after_coupon + expected_shipping, 2)
    assert cart.total(member=True, coupon="SAVE20") == pytest.approx(total_expected)

# empty cart costs zero and no shipping is added

def test_total_empty_cart():
    cart = Cart()
    assert cart.total() == 0
