import pytest
import math
import cart

# Helper functions

def approx_equal(a, b, rel_tol=1e-9, abs_tol=0.01):
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

# ---------- apply_discount tests ----------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (150, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (30, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
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
    [0, -1],
)
def test_bulk_discount_percent_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        ("  SaVe30  ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAV10", "SAVE0", "SAVE51", "save-5", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1500, False, 0),
        (500, False, 60),
        (900, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 100, quantity=3)
    assert c.items() == {"apple": 3}
    # add more of same item
    c.add_item("apple", 100, quantity=2)
    assert c.items() == {"apple": 5}
    # unit price mismatch raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 120)


def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item("banana", 50, quantity=4)
    c.remove_item("banana")  # remove one
    assert c.items() == {"banana": 3}
    c.remove_item("banana", quantity=3)  # remove remaining
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")


def test_cart_subtotal_single_item():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=10)  # 5% bulk discount
    line_total = 200 * 10
    expected_after_discount = cart.apply_discount(line_total, 5)
    assert math.isclose(c.subtotal(), round(expected_after_discount, 2), abs_tol=1e-9)


def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("itemA", 50, quantity=12)   # 5% bulk discount
    c.add_item("itemB", 30, quantity=3)    # no bulk
    line_total_a = 50 * 12
    line_total_b = 30 * 3
    sub_a = cart.apply_discount(line_total_a, 5)
    expected_total = round(sub_a + line_total_b, 2)
    assert c.subtotal() == expected_total


def test_cart_total_without_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("gadget", 200, quantity=10)  # subtotal after discount: 1900
    assert c.subtotal() == 1900.0
    # non-member with subtotal >=1000 => free shipping
    assert c.total(member=False) == 1900.0


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("product", 200, quantity=10)  # subtotal after discount: 1900
    total = c.total(member=False, coupon="SAVE50")
    # discounted amount 950; shipping 60 => total 1010
    assert total == 1010.0


def test_cart_total_member_half_shipping_after_coupon():
    c = cart.Cart()
    c.add_item("product", 200, quantity=10)  # subtotal after discount: 1900
    total = c.total(member=True, coupon="SAVE50")
    # discounted amount 950; shipping 30 (half for member) => total 980
    assert total == 980.0


def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
    assert c.subtotal() == 0
    # adding invalid items shouldn't affect
    with pytest.raises(ValueError):
        c.add_item("bad", -10)
