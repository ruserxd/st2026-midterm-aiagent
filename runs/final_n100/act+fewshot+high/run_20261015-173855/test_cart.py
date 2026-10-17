import pytest
import cart

# -------------------------------
# Tests for standalone functions
# -------------------------------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (123.456, 10, round(123.456 * 0.9, 2)),
        (100.00, 33, round(100.00 * 0.67, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected


@pytest.mark.parametrize(
    "price,percent",
    [
        (-10, 20),
        (50, -5),
        (75, 101),
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected


@pytest.mark.parametrize(
    "quantity",
    [
        -1,
        0,
    ],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)


@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("   save05 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected


@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",
        "SAVE51",
        "BADCODE",
        None,
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
        (200, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected


@pytest.mark.parametrize(
    "subtotal",
    [
        -1,
        -100.50,
    ],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)


# -------------------------------
# Tests for Cart class
# -------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()


def test_add_item_and_items(empty_cart):
    empty_cart.add_item("apple", 1.00, quantity=5)
    assert empty_cart.items() == {"apple": 5}

    # Adding more of same item increments quantity
    empty_cart.add_item("apple", 1.00, quantity=3)
    assert empty_cart.items() == {"apple": 8}

    # Adding a new different item
    empty_cart.add_item("banana", 2.50, quantity=2)
    assert set(empty_cart.items().keys()) == {"apple", "banana"}
    assert empty_cart.items()["banana"] == 2


def test_add_item_invalid_price_and_quantity(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", -1.00, quantity=3)

    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.00, quantity=0)

    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.00, quantity=-2)


def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("apple", 1.00, quantity=2)
    with pytest.raises(ValueError):
        empty_cart.add_item("apple", 1.50, quantity=1)


def test_remove_item_and_items(empty_cart):
    empty_cart.add_item("pear", 0.75, quantity=4)
    empty_cart.remove_item("pear", quantity=2)  # still remains
    assert empty_cart.items() == {"pear": 2}

    empty_cart.remove_item("pear", quantity=3)  # removes completely
    assert empty_cart.items() == {}

    with pytest.raises(KeyError):
        empty_cart.remove_item("pear")


def test_subtotal_single_and_bulk(empty_cart):
    # No bulk discount
    empty_cart.add_item("item1", 10.00, quantity=5)
    assert empty_cart.subtotal() == round(10.0 * 5, 2)

    # Bulk discount applies (quantity >=10)
    new_cart = cart.Cart()
    new_cart.add_item("item2", 20.0, quantity=12)  # bulk 5%
    expected_total = 20.0 * 12
    discounted = round(expected_total - expected_total * 0.05, 2)
    assert new_cart.subtotal() == discounted


def test_subtotal_multiple_items(empty_cart):
    empty_cart.add_item("apple", 1.00, quantity=5)   # no discount
    empty_cart.add_item("banana", 2.00, quantity=10)  # 5% discount
    subtotal_expected = round(
        (1.00 * 5) + (20.0 - 20.0 * 0.05), 2)
    assert empty_cart.subtotal() == subtotal_expected


def test_subtotal_empty():
    assert cart.Cart().subtotal() == 0

@pytest.mark.parametrize(
    "items,member,coupon,total_expected",
    [
        # Empty cart
        ([], False, None, 0),

        # No coupon, no member
        ([("item", 50.0, 5)], False, None, round(50.0 * 5 + 60, 2)),

        # Member only
        ([("item", 50.0, 5)], True, None, round(50.0 * 5 + 30, 2)),

        # Coupon only (10%)
        ([("item", 50.0, 5)], False, "SAVE10",
         round((250.0 * 0.9) + 60, 2)),

        # Member + coupon
        ([("item", 50.0, 5)], True, "SAVE10",
         round((250.0 * 0.9) + 30, 2)),

        # Subtotal above shipping threshold, no coupon
        ([("expensive", 200.0, 6)], False, None,
         round(1200.0, 2)),  # shipping free

        # Subtotal above threshold but coupon reduces below threshold
        ([("expensive", 200.0, 6)], False, "SAVE20",
         round((1200.0 * 0.8) + 60, 2)),
    ],
)
def test_total_variations(empty_cart, items, member, coupon, total_expected):
    # Build cart
    for name, unit_price, quantity in items:
        empty_cart.add_item(name, unit_price, quantity)

    if coupon is not None:
        assert empty_cart.total(member=member, coupon=coupon) == total_expected
    else:
        assert empty_cart.total(member=member) == total_expected


def test_total_invalid_coupon(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")


def test_total_shipping_after_coupon():
    # Create cart where subtotal > 1000 but after coupon it drops below threshold
    c = cart.Cart()
    c.add_item("expensive", 200.0, quantity=6)  # subtotal 1200

    expected_amount_after_discount = round(1200 * 0.8, 2)
    shipping_fee = 60
    total_expected = round(expected_amount_after_discount + shipping_fee, 2)

    assert c.total(coupon="SAVE20") == total_expected


def test_total_empty_cart():
    # Empty cart should return 0 even if coupon or member provided
    assert cart.Cart().total() == 0
    assert cart.Cart().total(member=True) == 0
    assert cart.Cart().total(coupon="SAVE10") == 0
    assert cart.Cart().total(member=True, coupon="SAVE10") == 0
