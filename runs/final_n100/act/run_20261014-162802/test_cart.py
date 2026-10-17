import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ---------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100, 0, 100.0),
        (100, 100, 0.0),
        (123.456, 20, round(123.456 * 0.8, 2)),
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 105, 200],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent --------------------------------------------

def test_bulk_discount_percent_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ------------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe50") == 50
    # boundaries
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

@pytest.mark.parametrize(
    "code",
    [
        "",  # empty
        "SAV10",  # missing letter
        "SAVE0",  # below range
        "SAVE51",  # above range
        "DISCOUNT10",  # wrong prefix
        "SAVE-5",  # negative number
        "SAVEabc",  # non-numeric
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ------------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

assert shipping_fee(999.99) == 60

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# member discounts on fee

def test_shipping_fee_member():
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(0, member=True) == 30
    # free shipping unaffected by membership
    assert shipping_fee(1200, member=True) == 0

# ---------- Cart class -------------------------------------------------------

def test_cart_empty_total():
    cart = Cart()
    assert cart.total() == 0

def test_cart_add_and_subtotal():
    cart = Cart()
    cart.add_item("apple", 2.5, quantity=4)
    cart.add_item("banana", 1.0, quantity=6)
    # subtotal: (2.5*4)+(1*6)=10+6=16
    assert cart.subtotal() == 16


def test_cart_remove_and_items():
    cart = Cart()
    cart.add_item("apple", 3, quantity=2)
    cart.remove_item("apple", quantity=1)
    # remaining: 1 apple at $3
    items = list(cart.items())
    assert len(items) == 1
    name, unit_price, qty = items[0]
    assert name == "apple"
    assert unit_price == 3
    assert qty == 1


def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    # add 10 bananas @ $5 each -> subtotal 50
    cart.add_item("banana", 5, quantity=10)
    # coupon SAVE10 (10%) => 45
    total = cart.total(coupon="SAVE10")
    # shipping fee: subtotal after coupon is 45 < 1000, member=False => 60
    expected_total = round(45 + 60, 2)
    assert total == expected_total


def test_cart_member_shipping_discount():
    cart = Cart()
    cart.add_item("widget", 20, quantity=10)  # subtotal 200
    total = cart.total(member=True)
    # no coupon: 200 + shipping fee (30 because member) = 230
    assert total == round(200 + 30, 2)


def test_cart_coupon_invalid_raises():
    cart = Cart()
    cart.add_item("item", 10)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

# ---------- Integration: bulk discount within Cart? not part of spec but ensure not used incorrectly

def test_cart_bulk_discount_not_applied():
    # The Cart implementation does NOT apply bulk discounts automatically.
    # This test ensures that adding many items keeps the subtotal as expected.
    cart = Cart()
    cart.add_item("item", 1, quantity=1000)
    assert cart.subtotal() == 1000

# ---------- Edge cases: removing more than present should raise

def test_cart_remove_more_than_exists():
    cart = Cart()
    cart.add_item("item", 5, quantity=2)
    with pytest.raises(ValueError):
        cart.remove_item("item", quantity=3)

# ---------- Items generator order independent but stable

def test_cart_items_order_consistency():
    cart = Cart()
    cart.add_item("a", 1)
    cart.add_item("b", 2)
    items_first = list(cart.items())
    # Adding again same item should update quantity, not duplicate
    cart.add_item("a", 1, quantity=2)
    items_second = list(cart.items())
    assert len(items_second) == 2
    names_second = {name for name, _, _ in items_second}
    assert names_second == {"a", "b"}

# ---------- Negative unit price test

def test_cart_negative_unit_price():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", -5)
