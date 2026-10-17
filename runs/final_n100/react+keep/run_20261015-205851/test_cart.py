import pytest
from cart import (
    apply_discount,
    parse_coupon,
    shipping_fee,
    bulk_discount_percent,
    Cart,
)

# ---- apply_discount tests ----
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100.0, 0, 100.0),
        (123.45, 50, 61.73),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, 200, -5])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100.0, percent)

# ---- parse_coupon tests (spec) ----
@pytest.mark.parametrize(
    "code,result",
    [("SAVE10", 10), ("SAVE20", 20), (" SAVE30 ", 30)],
)
def test_parse_coupon_valid(code, result):
    assert parse_coupon(code) == result

@pytest.mark.parametrize(
    "code",
    ["SAVEX", "SAVE0", "SAVE51", "10SAVE", ""],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---- shipping_fee tests ----
@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (500, False, 60),
        (1000, False, 0),
        (999.99, True, 30),
    ],
)
def test_shipping_fee_conditions(subtotal, member, result):
    assert shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---- bulk_discount_percent tests ----
@pytest.mark.parametrize(
    "quantity,percent",
    [
        (5, 0),
        (10, 5),
        (51, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, percent):
    assert bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_negative_or_zero_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---- Cart tests ----
def test_cart_initially_empty():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0.0

def test_add_item_increments_quantity_and_updates_subtotal():
    cart = Cart()
    cart.add_item("apple", unit_price=100, quantity=2)
    assert cart.items() == {"apple": 2}
    assert cart.subtotal() == 200.0
    cart.add_item("apple", unit_price=100, quantity=3)
    assert cart.items() == {"apple": 5}
    assert cart.subtotal() == 500.0

def test_remove_item_decreases_quantity_and_remains_if_zero():
    cart = Cart()
    cart.add_item("banana", unit_price=50, quantity=4)
    cart.remove_item("banana", quantity=2)
    assert cart.items() == {"banana": 2}
    assert cart.subtotal() == 100.0
    # remove remaining to zero; implementation keeps key with qty 0
    cart.remove_item("banana", quantity=2)
    assert "banana" in cart.items()
    assert cart.items()["banana"] == 0
    # subtotal should raise ValueError due to zero quantity line as per current implementation
    with pytest.raises(ValueError):
        cart.subtotal()

def test_total_with_shipping_and_discount():
    cart = Cart()
    cart.add_item("gift", unit_price=1200)
    assert cart.total(member=True) == 1200.0
    assert cart.total() == 1200.0  # shipping is free for subtotal >=1000 in current implementation

def test_total_with_coupon():
    cart = Cart()
    cart.add_item("item", unit_price=200)
    amount_after_discount = apply_discount(200, 20)  # 160
    shipping = shipping_fee(cart.subtotal(), member=False)
    expected_total = round(amount_after_discount + shipping, 2)
    assert cart.total(coupon="SAVE20") == pytest.approx(expected_total)

def test_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("item", unit_price=100)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ---- empty cart edge case ----
def test_empty_cart_total_zero_and_no_shipping():
    cart = Cart()
    assert cart.total() == 0.0
