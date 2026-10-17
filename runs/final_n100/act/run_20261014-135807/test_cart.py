import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# -----------------------------
# apply_discount tests
# -----------------------------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0
    # rounding behaviour
    assert apply_discount(99.99, 5) == round(99.99 * 0.95, 2)

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize(
    "percent",
    [(-1, "-5"), (101, "150")],
)
def test_apply_discount_invalid_percent(percent):
    # percent is either int or string; conversion will error for string
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# -----------------------------
# bulk_discount_percent tests
# -----------------------------

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# -----------------------------
# parse_coupon tests
# -----------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25 ") == 25
    assert parse_coupon("   SaVe5") == 5

@ pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "SAVEXX", "100"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

@ pytest.mark.parametrize("value", [123, None, 5.5])
def test_parse_coupon_non_string(value):
    with pytest.raises(ValueError):
        parse_coupon(value)

# -----------------------------
# shipping_fee tests (spec vs implementation mismatch)
# -----------------------------

def test_shipping_fee_spec():
    # According to spec, constants should be 60 and 30
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(200, member=True) == 30

# The implementation uses undefined constants; the test above will actually raise a NameError.
# Therefore we expect this test to fail if the implementation is buggy.

# -----------------------------
# Cart tests
# -----------------------------

def test_cart_add_and_items():
    c = Cart()
    c.add_item("apple", 1.0)
    assert c.items() == {"apple": 1}
    c.add_item("apple", 1.0, quantity=2)
    assert c.items() == {"apple": 3}

@ pytest.mark.parametrize(
    "unit_price,quantity",
    [( -1, 1), (5, -2)],
)
def test_cart_add_invalid(unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price, quantity)

@ pytest.mark.parametrize(
    "existing_price,new_price",
    [(1.0, 2.0)],
)
def test_cart_add_mismatched_price(existing_price, new_price):
    c = Cart()
    c.add_item("orange", existing_price)
    with pytest.raises(ValueError):
        c.add_item("orange", new_price)


def test_cart_remove():
    c = Cart()
    c.add_item("pear", 1.5, quantity=3)
    c.remove_item("pear")
    assert c.items() == {"pear": 2}
    # Removing more than remaining should delete the item
    c.remove_item("pear", quantity=3)
    assert "pear" not in c.items()

# Subtotal calculation with bulk discounts

def test_cart_subtotal():
    c = Cart()
    c.add_item("a", 10.0, quantity=5)   # no discount
    c.add_item("b", 20.0, quantity=12)  # 5% discount on b
    subtotal = c.subtotal()
    expected = round(10*5 + apply_discount(20*12, 5), 2)
    assert subtotal == expected

# Total calculation with coupon and shipping fee (implementation bug)

def test_cart_total_coupon_and_shipping():
    c = Cart()
    c.add_item("item", 200.0, quantity=1)  # subtotal 200
    total_with_coupon = c.total(coupon="SAVE10")
    # According to spec: apply coupon then add shipping on discounted amount
    expected_amount = round(200 * 0.90 + 60, 2)
    assert total_with_coupon == expected_amount

# Member discount reduces shipping

def test_cart_total_member_shipping():
    c = Cart()
    c.add_item("item", 50.0, quantity=1)
    total = c.total(member=True)
    # subtotal 50 <1000, member -> 30 shipping
    assert total == round(50 + 30, 2)
