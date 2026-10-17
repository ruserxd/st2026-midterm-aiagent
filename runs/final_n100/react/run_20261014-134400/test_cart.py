import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------
# Tests for apply_discount
# ---------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),           # example from spec
        (100, 0, 100.0),            # no discount
        (50, 100, 0.0),             # full discount
        (123.456, 20, round(123.456 * 0.8, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize("percent", ["fifty", None, -5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------------------
# Tests for bulk_discount_percent
# ---------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),      # less than 10
        (9, 0),      # edge case
        (10, 5),     # >=10 but <50
        (49, 5),
        (50, 10),    # >=50 but <100
        (99, 10),
        (100, 15),   # >=100
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------------------
# Tests for parse_coupon
# ---------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save10", 10),            # case-insensitive
        (" SAVE20 ", 20),           # surrounding whitespace
        ("Save50", 50),             # max allowed value
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "", "  ", "ABCD10"]) 

def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------------------
# Tests for shipping_fee
# ---------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),          # free shipping at $1000
        (1500, True, 0),           # members pay half but still free over $1000
        (200, True, 30),           # member gets half of 60
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------------------
# Tests for Cart class basics
# ---------------------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    assert c.items()["apple"] == (1.0, 3)
    c.add_item("banana", 0.5)   # default quantity 1
    assert c.items()["banana"] == (0.5, 1)


def test_cart_remove_and_subtotal():
    c = Cart()
    c.add_item("apple", 2.0, 5)
    c.add_item("orange", 3.0, 2)
    assert c.subtotal() == 2.0*5 + 3.0*2
    # remove one apple
    c.remove_item("apple")
    assert c.items()["apple"] == (2.0, 4)
    # remove two oranges -> should remove key completely
    c.remove_item("orange", 2)
    assert "orange" not in c.items()

# Edge case: removing more than present
@pytest.mark.xfail(reason="Implementation may not support over-removal yet")
def test_cart_remove_more_than_exists():
    c = Cart()
    c.add_item("pen", 1.5, 2)
    # attempting to remove more than quantity might raise ValueError or ignore
    with pytest.raises(ValueError):
        c.remove_item("pen", 3)

# Test total: ensure it applies discounts correctly according to the inferred rules.
# Since specification for total is not fully detailed, we keep these tests as sanity checks.

def test_cart_total_basic():
    c = Cart()
    c.add_item("widget", 100.0, 10)   # bulk discount of 5% should apply
    assert c.total() == pytest.approx(
        shipping_fee(1000) + apply_discount(100*10, bulk_discount_percent(10))
    )

# Test with member and coupon

def test_cart_total_with_member_and_coupon():
    c = Cart()
    c.add_item("gadget", 200.0, 50)   # bulk discount 10%
    subtotal = 200*50
    discounted_subtotal = apply_discount(subtotal, bulk_discount_percent(50))
    shipping = shipping_fee(discounted_subtotal, member=True)
    coupon_discount = parse_coupon("SAVE20")
    final_total = discounted_subtotal + shipping
    final_total = apply_discount(final_total, coupon_discount)
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(final_total)
