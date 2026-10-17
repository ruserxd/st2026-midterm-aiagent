import pytest
import cart

# ----------
# Tests for utility functions: apply_discount, bulk_discount_percent,
# parse_coupon, shipping_fee
# ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (10.0, 5, 9.5),
        (100.0, 20, 80.0),
        (123.45, 25, round(123.45 * 0.75, 2)),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [
        (-1, 10),       # negative price
        (10, -5),       # negative percent
        (10, 105),      # percent >100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----------
# bulk_discount_percent
# ----------

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
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [
        -1,
        0,
        2.5,
        "10",
    ],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----------
# parse_coupon
# ----------

@pytest.mark.parametrize(
    "code,percent",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SaVe30  ", 30),
    ],
)
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize(
    "code",
    [
        "SAVEX",     # non-numeric
        "SAVE0",      # below 1
        "SAVE51",     # above 50
        "",           # empty string
        "1234",       # not a SAVE code
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----------
# shipping_fee
# ----------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (950, False, 60),
        (950, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [
        -1,
        -100,
    ],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----------
# Cart class tests
# ----------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 2.5, 3)
    assert c.items() == {"apple": 3}
    # Add same item again with same unit price
    c.add_item("apple", 2.5, 2)
    assert c.items() == {"apple": 5}


def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        # negative unit price
        c.add_item("orange", -1, 3)
    with pytest.raises(ValueError):
        # zero quantity
        c.add_item("orange", 1.0, 0)
    with pytest.raises(ValueError):
        # non-integer quantity (float)
        c.add_item("orange", 1.0, 2.5)
    with pytest.raises(ValueError):
        # negative quantity
        c.add_item("orange", 1.0, -3)
    # mismatched unit price for existing item
    c.add_item("banana", 1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 2.0, 1)


def test_cart_remove_reduces_quantity():
    c = cart.Cart()
    c.add_item("pear", 1.5, 4)
    c.remove_item("pear", 2)
    assert c.items() == {"pear": 2}


def test_cart_remove_all_removes_item():
    c = cart.Cart()
    c.add_item("cherry", 3.0, 3)
    c.remove_item("cherry", 3)
    # The item should be completely removed from the cart.
    assert "cherry" not in c.items()


def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("date", 1)


def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("orange", 10.0, 2)
    assert c.subtotal() == 20.0


def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("sugar", 5.0, 12)  # bulk discount 5%
    expected = round(5.0 * 12 * (1 - 0.05), 2)
    assert c.subtotal() == expected


def test_cart_subtotal_empty_returns_zero():
    c = cart.Cart()
    assert c.subtotal() == 0


def test_cart_total_empty_is_zero():
    c = cart.Cart()
    assert c.total() == 0


def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("banana", 50.0, 1)
    # subtotal=50, shipping fee=60 -> total 110
    assert c.total() == 110.0


def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("banana", 50.0, 1)
    # subtotal=50, shipping fee=30 -> total 80
    assert c.total(member=True) == 80.0


def test_cart_total_coupon_no_threshold_change():
    c = cart.Cart()
    c.add_item("item", 200.0, 4)  # subtotal=800
    # coupon SAVE10 reduces by 10% -> 720; shipping fee on 720 <1000 => 60
    assert c.total(coupon="SAVE10") == 780.0

@pytest.mark.parametrize(
    "member,expected_total",
    [
        (False, 940.0),   # non-member: shipping fee 60
        (True, 910.0),    # member: shipping fee 30
    ],
)
def test_cart_total_coupon_threshold_bug(member, expected_total):
    c = cart.Cart()
    c.add_item("expensive", 550.0, 2)  # subtotal=1100
    assert c.total(member=member, coupon="SAVE20") == expected_total


def test_cart_total_coupon_exact_threshold_bug():
    c = cart.Cart()
    c.add_item("exact", 500.0, 2)  # subtotal=1000
    assert c.total(coupon="SAVE10") == 960.0
