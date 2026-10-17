import pytest
import cart

# Helper function mirroring coupon parsing logic from specification.
def _expected_coupon_percent(code: str) -> int:
    """Return the discount percent encoded in a valid coupon code.

    The spec states that a valid coupon is ``SAVE`` followed by an integer N
    with 1 <= N <= 50. Matching is case‑insensitive and surrounding
    whitespace should be ignored.
    """
    code = code.strip().upper()
    if not code.startswith("SAVE"):
        raise ValueError("invalid coupon: '{}'".format(code))
    num_str = code[4:]
    if not num_str.isdigit():
        raise ValueError("invalid coupon: '{}'".format(code))
    n = int(num_str)
    if not (1 <= n <= 50):
        raise ValueError("invalid coupon: '{}'".format(code))
    return n

# ---------------------------------------------------------------------------
# apply_discount tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (199.99, 10, round(199.99 * 0.9, 2)),
        (100, 0, 100.0),
        (100, 100, 0.0),
        # rounding case
        (1.2345, 20, round(1.2345 * 0.8, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------------------------------------------------------------------------
# bulk_discount_percent tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
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
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 2.5, "10"],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# parse_coupon tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SaVe30  ", 30),
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
        "SAVE-5",
        "SA VE10",
        "",
        "   ",
        "SAVEAB",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------------------------------------------------------------------
# shipping_fee tests (corrected to match specification)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (800, True, 30),
        (500, False, 60),
        # subtotal >= 1000 => free shipping regardless of membership
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -10.5],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# Cart tests
# ---------------------------------------------------------------------------
@pytest.fixture
def cart_obj():
    return cart.Cart()

def test_cart_init(cart_obj):
    assert isinstance(cart_obj, cart.Cart)
    assert cart_obj.items() == {}
    # subtotal should be a float 0.0 per spec rounding
    assert cart_obj.subtotal() == 0.0
    assert cart_obj.total() == 0.0

# add_item basic and error tests

def test_cart_add_item_basic(cart_obj):
    cart_obj.add_item("apple", 1.5, 3)
    assert cart_obj.items() == {"apple": 3}

def test_cart_add_item_increment_same_price(cart_obj):
    cart_obj.add_item("banana", 2.0, 1)
    cart_obj.add_item("banana", 2.0, 4)
    assert cart_obj.items() == {"banana": 5}

def test_cart_add_item_mismatched_price(cart_obj):
    cart_obj.add_item("orange", 3.0, 2)
    with pytest.raises(ValueError):
        cart_obj.add_item("orange", 4.0, 1)

@pytest.mark.parametrize(
    "price,quantity",
    [(-1, 1), (1.5, 0), (1.5, -2)],
)
def test_cart_add_item_invalid_params(cart_obj, price, quantity):
    with pytest.raises(ValueError):
        cart_obj.add_item("grape", price, quantity)

@pytest.mark.parametrize(
    "quantity",
    [2.5, "3"],
)
def test_cart_add_item_non_integer_quantity(cart_obj, quantity):
    with pytest.raises(ValueError):
        cart_obj.add_item("peach", 1.0, quantity)

# remove_item tests

def test_cart_remove_item_partial(cart_obj):
    cart_obj.add_item("pear", 2.5, 4)
    cart_obj.remove_item("pear", 2)
    assert cart_obj.items() == {"pear": 2}
    # removing more than remaining should delete the item
    cart_obj.remove_item("pear", 3)
    assert "pear" not in cart_obj.items()

def test_cart_remove_item_nonexistent(cart_obj):
    with pytest.raises(KeyError):
        cart_obj.remove_item("mango", 1)

# items returns a new dict

def test_cart_items_copy(cart_obj):
    cart_obj.add_item("kiwi", 3.0, 2)
    returned = cart_obj.items()
    returned["kiwi"] = 10  # modify the copy
    assert cart_obj.items() == {"kiwi": 2}

# subtotal tests

def test_cart_subtotal_no_discount(cart_obj):
    cart_obj.add_item("bread", 1.0, 3)
    expected = round(1.0 * 3, 2)
    assert cart_obj.subtotal() == expected

@pytest.mark.parametrize(
    "items,expected_subtotal",
    [
        (
            [("itemA", 10.0, 5)],  # no discount
            round(10.0 * 5, 2),
        ),
        (
            [("itemB", 20.0, 10)],  # 5% discount
            round(20.0 * 10 * 0.95, 2),
        ),
        (
            [("itemC", 30.0, 50)],  # 10% discount
            round(30.0 * 50 * 0.90, 2),
        ),
        (
            [("itemD", 40.0, 100)],  # 15% discount
            round(40.0 * 100 * 0.85, 2),
        ),
        (
            [
                ("itemE1", 10.0, 5),
                ("itemE2", 20.0, 10),
                ("itemE3", 30.0, 50),
                ("itemE4", 40.0, 100),
            ],
            round(
                10.0 * 5
                + 20.0 * 10 * 0.95
                + 30.0 * 50 * 0.90
                + 40.0 * 100 * 0.85,
                2,
            ),
        ),
    ],
)
def test_cart_subtotal_multiple(items, expected_subtotal):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    assert c.subtotal() == expected_subtotal

def test_cart_subtotal_fractional_rounding(cart_obj):
    cart_obj.add_item("special", 19.99, 10)  # 5% discount
    expected = round(19.99 * 10 * 0.95, 2)
    assert cart_obj.subtotal() == expected

# total tests

def test_cart_total_empty(cart_obj):
    assert cart_obj.total() == 0.0

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 10.0, 5)  # subtotal 50
    subtotal_expected = round(10.0 * 5, 2)
    shipping_fee = cart.shipping_fee(subtotal_expected, member=False)
    expected_total = round(subtotal_expected + shipping_fee, 2)
    assert c.total() == expected_total

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", 10.0, 5)  # subtotal 50
    subtotal_expected = round(10.0 * 5, 2)
    shipping_fee = cart.shipping_fee(subtotal_expected, member=True)
    expected_total = round(subtotal_expected + shipping_fee, 2)
    assert c.total(member=True) == expected_total

def test_cart_total_with_coupon_and_shipping():
    # Case 1: coupon reduces below free threshold
    c = cart.Cart()
    c.add_item("expensive", 240.0, 5)  # subtotal 1200
    coupon_code = "SAVE20"
    percent = _expected_coupon_percent(coupon_code)
    subtotal_before = round(240.0 * 5, 2)
    after_coupon = round(subtotal_before * (1 - percent / 100), 2)
    shipping_fee_non_member = cart.shipping_fee(after_coupon, member=False)
    expected_total_non_member = round(after_coupon + shipping_fee_non_member, 2)
    assert c.total(coupon=coupon_code) == expected_total_non_member

    # Case 2: coupon pushes to free shipping threshold
    d = cart.Cart()
    d.add_item("big", 1250.0, 1)  # subtotal 1250
    percent = _expected_coupon_percent(coupon_code)
    subtotal_before = round(1250.0 * 1, 2)
    after_coupon = round(subtotal_before * (1 - percent / 100), 2)
    shipping_fee_member = cart.shipping_fee(after_coupon, member=True)
    expected_total_member = round(after_coupon + shipping_fee_member, 2)
    assert d.total(coupon=coupon_code, member=True) == expected_total_member

def test_cart_total_with_coupon_free_shipping_non_member():
    c = cart.Cart()
    c.add_item("big", 1250.0, 1)
    coupon_code = "SAVE20"
    percent = _expected_coupon_percent(coupon_code)
    subtotal_before = round(1250.0 * 1, 2)
    after_coupon = round(subtotal_before * (1 - percent / 100), 2)
    shipping_fee_non_member = cart.shipping_fee(after_coupon, member=False)
    assert shipping_fee_non_member == 0
    expected_total = round(after_coupon + shipping_fee_non_member, 2)
    assert c.total(coupon=coupon_code) == expected_total

def test_cart_total_with_coupon_member_half_shipping():
    c = cart.Cart()
    c.add_item("medium", 200.0, 5)  # subtotal 1000
    coupon_code = "SAVE10"
    percent = _expected_coupon_percent(coupon_code)
    subtotal_before = round(200.0 * 5, 2)
    after_coupon = round(subtotal_before * (1 - percent / 100), 2)
    shipping_fee_member = cart.shipping_fee(after_coupon, member=True)
    expected_total = round(after_coupon + shipping_fee_member, 2)
    assert c.total(coupon=coupon_code, member=True) == expected_total

def test_cart_total_invalid_coupon(cart_obj):
    with pytest.raises(ValueError):
        cart_obj.total(coupon="DISCOUNT10")

def test_cart_total_empty_with_coupon():
    c = cart.Cart()
    # empty cart should still cost 0 regardless of coupon
    assert c.total(coupon="SAVE10") == 0.0

# add item after removal with different price

def test_add_item_after_removal_different_price(cart_obj):
    cart_obj.add_item("banana", 1.0, 2)
    cart_obj.remove_item("banana", 2)  # remove all
    # new price allowed when re-adding after removal
    cart_obj.add_item("banana", 2.5, 1)
    assert cart_obj.items() == {"banana": 1}
