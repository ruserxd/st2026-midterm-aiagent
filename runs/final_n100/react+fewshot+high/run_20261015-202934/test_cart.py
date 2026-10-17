import pytest
import cart

@pytest.fixture
def empty_cart():
    return cart.Cart()


# Tests for apply_discount
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (123.45, 10, round(123.45 * 0.9, 2)),
        (50, 0, 50.0),
        (100.5, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected


@pytest.mark.parametrize(
    "price,percent",
    [
        (-1, 10),
        (50, -5),
        (50, 101),
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


# Tests for bulk_discount_percent
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (101, 15),
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected


@pytest.mark.parametrize(
    "quantity",
    [
        -1,
        0,
        -10,
        "ten",
    ],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)


# Tests for parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("SaVe1", 1),
        ("SAVE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected


@pytest.mark.parametrize(
    "code",
    [
        "DISCOUNT10",
        "SAVE0",
        "SAVE51",
        "",
        "saveabc",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


# Tests for shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (1000, True, 0),
        (999.99, True, 30),
    ],
)
def test_shipping_fee_valid(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected


@pytest.mark.parametrize(
    "subtotal",
    [
        -1,
        -50,
    ],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)


# Cart method tests
def test_cart_add_item_new(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}
    assert c.subtotal() == round(1.5 * 2, 2)  # 3.0


def test_cart_add_existing_same_price(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 2)
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == round(1.5 * 5, 2)  # 7.5


def test_cart_add_existing_diff_price(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 1)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)


def test_cart_add_negative_unitprice(empty_cart):
    c = empty_cart
    with pytest.raises(ValueError):
        c.add_item("apple", -5.0, 1)


@pytest.mark.parametrize(
    "quantity",
    [
        0,
        -3,
        2.5,
    ],
)
def test_cart_add_invalid_quantity(empty_cart, quantity):
    c = empty_cart
    with pytest.raises(ValueError):
        c.add_item("apple", 1.0, quantity)


def test_cart_remove_less_than_existing(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 5)
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == round(1.5 * 3, 2)  # 4.5


def test_cart_remove_exact_quantity(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 5)
    c.remove_item("apple", 5)
    # Spec: item removed entirely; items() should be {}
    assert c.items() == {}


def test_cart_remove_more_than_existing(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.5, 3)
    c.remove_item("apple", 10)
    assert c.items() == {}


def test_cart_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexist", 1)


def test_cart_subtotal_empty(empty_cart):
    assert empty_cart.subtotal() == 0


def test_cart_subtotal_single_no_discount(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 5)
    assert c.subtotal() == round(1.0 * 5, 2)  # 5.0


def test_cart_subtotal_bulk_discount(empty_cart):
    c = empty_cart
    c.add_item("banana", 2.0, 10)
    expected = round(2.0 * 10 * (1 - 0.05), 2)  # 20 * 0.95 =19.0
    assert c.subtotal() == expected


def test_cart_subtotal_multiple_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 3.0, 6)
    c.add_item("banana", 4.0, 15)
    # apple: line_total=18* discount 0 => 18
    # banana: line_total=60*discount 5% => apply_discount(60,5) = round(60*0.95,2)=57.0
    expected = round(18 + 57.0, 2)
    assert c.subtotal() == expected


def test_cart_total_empty(empty_cart):
    assert empty_cart.total() == 0


def test_cart_total_no_coupon_non_member(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 5)
    expected = round(5.0 + 60, 2)  # 65.0
    assert c.total() == expected


def test_cart_total_no_coupon_member(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 5)
    expected = round(5.0 + 30, 2)  # 35.0
    assert c.total(member=True) == expected


def test_cart_total_with_coupon_threshold_crossing(empty_cart):
    c = empty_cart
    # add items: subtotal >1000 before coupon
    c.add_item("expensive", 200.0, 5)   # 1000
    c.add_item("tiny", 10.0, 1)         # +10 => 1010
    # apply coupon 20%
    total_expected = round(808.0 + 60.0, 2)  # discounted 808, shipping 60 -> 868
    assert c.total(coupon="SAVE20") == total_expected


def test_cart_total_invalid_coupon(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALIDCODE")
