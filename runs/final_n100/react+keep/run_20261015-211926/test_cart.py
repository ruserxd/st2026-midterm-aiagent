import pytest
import cart

# ---------- apply_discount ----------------------------------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (123.45, 5, round(123.45 * 0.95, 2)),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize(
    "price",
    [-1, -100.5],
)
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError, match="price must be non-negative"):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-1, 101, 150],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError, match="percent must be between 0 and 100"):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ---------------------------------------

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),     # below threshold
        (10, 5),    # threshold at 10
        (49, 5),
        (50, 10),   # threshold at 50
        (99, 10),
        (100, 15),  # threshold at 100
        (150, 15),
    ],
)
def test_bulk_discount_percent_expected(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 1.2, "10"],
)
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError, match="quantity must be a positive integer"):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------

@pytest.mark.parametrize(
    "code,result",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("   SAVE20  ", 20),
    ],
)
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize(
    "code",
    ["10SAVE", "SA VE10", "SAVE0", "SAVE51", "SAVE-5", 123],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError, match="invalid coupon"):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200, False, 0),      # free shipping threshold
        (1200, True, 0),       # free shipping also for members
        (800, False, 60),      # non-member standard fee
        (800, True, 30),       # member half price
    ],
)
def test_shipping_fee_expected(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100.5],
)
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        cart.shipping_fee(subtotal, False)

# ---------- Cart class -----------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # Adding same item increases quantity
    c.add_item("APPLE", 1.0, 2)  # note case difference -> should be considered separate name
    assert c.items() == {"apple": 3, "APPLE": 2}
    # Adding with different unit price raises ValueError
    with pytest.raises(ValueError, match="unit price does not match existing item"):
        c.add_item("apple", 1.5, 1)


def test_cart_remove_and_quantity():
    c = cart.Cart()
    c.add_item("banana", 0.5, 10)
    # remove less than quantity
    c.remove_item("banana", 4)
    assert c.items() == {"banana": 6}
    # remove more than remaining quantity should delete item
    c.remove_item("banana", 10)
    assert "banana" not in c.items()
    # removing nonexistent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("cherry", 1)


def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("widget", 10.0, 9)   # no bulk discount
    assert c.subtotal() == pytest.approx(90.0)
    c.remove_item("widget")        # remove one unit (now quantity 8)
    assert c.subtotal() == pytest.approx(80.0)
    # Add enough to trigger bulk discount of 5%
    for _ in range(2):
        c.add_item("widget", 10.0, 1)  # quantity back to 10
    assert c.items()["widget"] == 10
    assert cart.bulk_discount_percent(10) == 5
    expected_total = 10.0 * 10
    discounted = expected_total * 0.95
    assert c.subtotal() == pytest.approx(round(discounted, 2))


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("gadget", 100.0, 1)
    # subtotal is 100 -> no shipping fee (since >= 1000 threshold not met yet; shipping should apply 60 or 30)
    assert c.subtotal() == pytest.approx(100.0)
    # total without coupon or membership
    assert c.total(member=False, coupon=None) == pytest.approx(round(100 + 60, 2))
    # total with coupon SAVE10 (10% off) and member
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(
        round((100 * 0.9) + 30, 2)
    )
    # total for empty cart should be zero
    empty_cart = cart.Cart()
    assert empty_cart.total() == 0

# ---------- Edge case: subtotal used twice in total implementation ---------
# This test checks that shipping_fee is applied to the amount after coupon.
# The specification states that shipping fee depends on the discounted subtotal,
# but the current implementation mistakenly passes the original subtotal.
# The following asserts the correct behavior; a failing test indicates the mismatch.


def test_total_shipping_after_coupon_expected_behavior():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    # Suppose coupon gives 50% off -> amount 50
    expected = round(50 + 60, 2)  # shipping based on discounted subtotal (no member)
    assert c.total(coupon="SAVE50") == pytest.approx(expected)
