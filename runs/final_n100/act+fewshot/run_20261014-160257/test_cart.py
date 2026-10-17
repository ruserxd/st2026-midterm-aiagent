import pytest
import cart

# helper to compute discounted price

def expect_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# ----- tests for standalone functions -----
@pytest.mark.parametrize(
    "price,percent,result",
    [
        # normal case
        (200.0, 15, expect_discount(200.0, 15)),
        # boundary cases
        (0.0, 0, 0.0),
        (100.0, 100, 0.0),
        (50.5, 1, round(50.5 * 0.99, 2)),
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [
        # negative price
        (-10.0, 20),
        # percent too low/high
        (100.0, -5),
        (200.0, 110),
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),   # below 10
        (10, 5),  # exactly 10
        (49, 5),  # between 10 and 50
        (50, 10), # exactly 50
        (99, 10), # just below 100
        (100, 15),
        (250, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [-1, 0, 2.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- coupon parsing -----
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30 ", 30),
        ("SAVE1", 1),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "",          # empty
        "SAVEXX",   # invalid suffix
        "SAVExx",   # non‑int suffix
        "SAVE0",    # out of range
        "SAVE51",   # out of range
        "INVALID",  # wrong prefix
        "  ",       # whitespace only
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping fee -----
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0.0, False, 60),
        (500.0, False, 60),
        (999.99, True, 30),
        (1000.0, False, 0),
        (1500.0, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10.0, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 2.0, quantity=3)
    assert empty_cart.items() == {"apple": 3}
    # subtotal includes bulk discount if any
    expected_subtotal = expect_discount(6.0, cart.bulk_discount_percent(3))
    assert empty_cart.subtotal() == expected_subtotal
    assert empty_cart.total() == empty_cart.subtotal()

def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana", 1.5)
    empty_cart.add_item("banana", 1.5, quantity=2)
    assert empty_cart.items() == {"banana": 3}
    assert round(empty_cart.total(), 2) == round(4.5, 2)

def test_add_item_same_name_different_price_raises(empty_cart):
    empty_cart.add_item("orange", 1.0)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.5)

@pytest.mark.parametrize(
    "name,quantity",
    [
        ("cherry", 0),   # zero quantity
        ("pear", -2),    # negative quantity
        ("plum", 1.5),   # non‑int
        ("grape", -1),   # negative
    ],
)
def test_add_item_invalid(empty_cart, name, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item(name, 0.99, quantity=quantity)

@pytest.mark.parametrize(
    "name,quantity",
    [
        ("peach", 5),
        ("berry", 2),
    ],
)
def test_remove_item_partial(empty_cart, name, quantity):
    empty_cart.add_item(name, 1.25, quantity=3)
    empty_cart.remove_item(name, quantity=quantity)
    assert empty_cart.items() == {name: 3 - quantity}

def test_remove_item_to_zero_and_beyond(empty_cart):
    empty_cart.add_item("melon", 0.5, quantity=2)
    empty_cart.remove_item("melon", quantity=2)
    assert "melon" not in empty_cart.items()
    with pytest.raises(KeyError):
        empty_cart.remove_item("melon")

def test_remove_nonexistent_raises(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")

@pytest.mark.parametrize(
    "member,coupon",
    [
        (False, None),
        (True, None),
        (False, "SAVE20"),
        (True, "SAVE5"),
    ],
)
def test_total_with_member_and_coupon(empty_cart, member, coupon):
    empty_cart.add_item("taco", 10.0, quantity=4)  # 40 total
    total = empty_cart.total(member=member, coupon=coupon)
    # compute expected subtotal with bulk discount per item (none for qty<10)
    expected_subtotal = expect_discount(10.0 * 4, cart.bulk_discount_percent(4))
    if coupon:
        discount_pct = cart.parse_coupon(coupon.strip())
    else:
        discount_pct = 0
    final = expect_discount(expected_subtotal, discount_pct)
    shipping = cart.shipping_fee(final, member=member)
    expected_total = round(final + shipping, 2)
    assert round(total, 2) == expected_total

def test_total_shoes_free_shipping(empty_cart):
    empty_cart.add_item("expensive", 250.0, quantity=5)  # subtotal before shipping >1000
    total = empty_cart.total()
    # bulk discount for qty=5 -> 0
    assert round(total, 2) == round(1250.0, 2)
