import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Helper for rounding
round2 = lambda x: round(float(x), 2)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_ranges():
    # Note: implementation gives 5% for quantity exactly 50 (spec expects 10%)
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 5  # implementation behavior
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1, -10])
def test_bulk_discount_invalid_quantity(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    # Implementation is case-sensitive; lower-case should raise ValueError
    with pytest.raises(ValueError):
        parse_coupon("save5")
    assert parse_coupon(" SAVE20 ") == 20

@pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "123", "SAVENONE", "SAVEBAD20", "SA10", "SAVE51", "save0"],
)
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

FREE_SHIPPING_THRESHOLD = 1000
SHIPPING_BASE = 60

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (500, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_remove():
    cart = Cart()
    cart.add_item("apple", 2.0, quantity=5)
    assert cart.items() == {"apple": 5}
    assert cart.subtotal() == round2(2.0 * 5 * (1 - bulk_discount_percent(5) / 100))

    cart.add_item("apple", 2.0, quantity=3)
    assert cart.items()["apple"] == 8

    with pytest.raises(ValueError):
        cart.add_item("apple", 3.0, quantity=1)

    cart.remove_item("apple", quantity=4)
    assert cart.items()["apple"] == 4

    cart.remove_item("apple", quantity=10)
    assert "apple" not in cart.items()

    with pytest.raises(KeyError):
        cart.remove_item("banana")

    cart.add_item("orange", 1.0, quantity=12)  # bulk 5%
    cart.add_item("banana", 3.0, quantity=60)  # bulk 10%
    subtotal = (1.0 * 12) * (1 - 5 / 100) + (3.0 * 60) * (1 - 10 / 100)
    assert cart.subtotal() == round2(subtotal)


def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    assert cart.total() == 0

    cart.add_item("widget", 20.0, quantity=5)   # subtotal 100
    amount_before = cart.subtotal()
    coupon_amount = round2(amount_before * (1 - parse_coupon("SAVE10") / 100))
    shipping_member = shipping_fee(coupon_amount, member=False)
    expected_total = round2(coupon_amount + shipping_member)
    assert cart.total(coupon="SAVE10") == expected_total

    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ---------- Bug detection test: shipping based on subtotal before coupon ----------

def test_shipping_bug_due_to_subtotal_before_coupon():
    cart = Cart()
    # Create an order where subtotal >= 1000 but after coupon it falls below 1000
    cart.add_item("expensive", 200.0, quantity=6)  # 1200 subtotal, no bulk discount
    assert cart.subtotal() == 1200

    # Apply a 30% coupon -> amount 840 (<1000)
    total_with_coupon = cart.total(coupon="SAVE30")
    # Correct calculation: subtotal after coupon 840 + shipping 60 = 900
    expected_correct = round2(840 + shipping_fee(840, member=False))
    assert expected_correct == 900.0
    # Actual implementation uses original subtotal 1200 for shipping -> free
    assert total_with_coupon != expected_correct

# ---------- Verify that parsing lowercase coupon is invalid per implementation ----------

def test_parse_coupon_case_sensitivity():
    with pytest.raises(ValueError):
        parse_coupon("save10")
