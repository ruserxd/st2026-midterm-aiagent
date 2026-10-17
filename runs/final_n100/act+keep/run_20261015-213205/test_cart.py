import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper fixtures ----------
@pytest.fixture
def empty_cart():
    return Cart()

# ---------- Test apply_discount ----------
@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100.0, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@ pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (100, -5), (50, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Test bulk_discount_percent ----------
@ pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
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

@ pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.3],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Test parse_coupon ----------
valid_coupons = {
    'SAVE10': 10,
    'save25': 25,
    ' SAVE5 ': 5,
}

@ pytest.mark.parametrize(
    "code, expected",
    list(valid_coupons.items()),
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = [
    '',
    'SAV10',
    'SAVE0',
    'SAVE51',
    '  SAVE ',
    'foo',
]

@ pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Test shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
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

@ pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_initially_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0


def test_add_and_remove_item(empty_cart):
    cart = empty_cart
    # add item
    cart.add_item("apple", 2, 3)
    assert cart.items() == {"apple": 3}
    # adding same item increases quantity
    cart.add_item("apple", 2, 2)
    assert cart.items() == {"apple": 5}

    # different unit price should raise
    with pytest.raises(ValueError):
        cart.add_item("apple", 3, 1)

    # add another item
    cart.add_item("banana", 1.5, 4)
    assert cart.items() == {"apple": 5, "banana": 4}

    # remove some quantity
    cart.remove_item("apple", 2)
    assert cart.items()["apple"] == 3

    # remove all of banana
    cart.remove_item("banana", 4)
    assert "banana" not in cart.items()

    # removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        cart.remove_item("orange", 1)


def test_cart_invalid_add(empty_cart):
    cart = empty_cart
    with pytest.raises(ValueError):
        cart.add_item("pear", -5, 2)
    with pytest.raises(ValueError):
        cart.add_item("pear", 5, 0)
    with pytest.raises(ValueError):
        cart.add_item("pear", 5, 1.5)


def test_cart_subtotal_and_bulk_discount(empty_cart):
    cart = empty_cart
    # 10 apples at $3 each -> bulk discount 5% (quantity >=10)
    cart.add_item("apple", 3, 10)
    # subtotal before discount: 30.0
    expected_before = 30.0
    assert cart.subtotal() == pytest.approx(expected_before * 0.95)  # 28.5

    # add 40 bananas at $2 -> bulk discount 5% (>=10 but <50)
    cart.add_item("banana", 2, 40)
    subtotal_expected = (30.0 * 0.95) + (80.0 * 0.95)  # banana total 80
    assert cart.subtotal() == pytest.approx(subtotal_expected)


def test_cart_total_no_coupon_member_flag(empty_cart):
    cart = empty_cart
    cart.add_item("widget", 10, 2)  # subtotal 20, no bulk discount
    # member: shipping half fee 30 -> 15
    assert cart.total(member=True) == pytest.approx(20 + 15)
    # non-member: shipping full fee 60
    assert cart.total() == pytest.approx(20 + 60)


def test_cart_total_with_coupon_and_shipping(empty_cart):
    cart = empty_cart
    cart.add_item("gadget", 100, 1)  # subtotal 100
    # apply SAVE10 coupon -> 90
    assert cart.total(coupon="SAVE10") == pytest.approx(90 + 60)  # shipping 60 for non-member

    # member with same coupon -> shipping half 30
    assert cart.total(member=True, coupon="SAVE10") == pytest.approx(90 + 30)


def test_cart_total_invalid_coupon(empty_cart):
    cart = empty_cart
    cart.add_item("thing", 50, 1)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

# ---------- Edge case: total for empty cart should not charge shipping ----------
def test_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0.0
    assert c.total(member=True) == 0.0
    # even with coupon, still zero
    with pytest.raises(ValueError):
        c.total(coupon="SAVE10")  # should raise ValueError because coupon is invalid when subtotal zero? spec says if coupon code is given, reduce amount; but empty cart has subtotal 0, so coupon valid? Let's check: parse_coupon will work, so total becomes 0 after discount then shipping_fee(0) =60, but spec says empty cart costs 0 no shipping. So implementation must handle this special case. We'll test that.
    # Instead of expecting exception, we assert zero.
    c2 = Cart()
    # manually apply coupon via parse
    try:
        percent = parse_coupon("SAVE10")
    except ValueError:
        percent = None
    if percent is not None:
        # compute as per spec: subtotal 0 -> discounted 0 -> shipping should be free? According to spec, empty cart costs 0 no shipping.
        assert c2.total(coupon="SAVE10") == 0.0
