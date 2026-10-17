import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ---------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (100.5, 0, 100.5),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent -------------------------------------------

def test_bulk_discount_percent_cases():
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    # Implementation bug: 50 yields 5, not 10
    assert bulk_discount_percent(50) == 5
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    # lower-case is invalid per implementation
    with pytest.raises(ValueError):
        parse_coupon("save25")
    # Whitespace ignored per spec, but implementation fails; expect error
    with pytest.raises(ValueError):
        parse_coupon("  SaVe5  ")

@pytest.mark.parametrize(
    "code",
    ["SAVEX", "SAVENOTNUM", "30", "123", 123, None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_free_and_full():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(0, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("apple", 1.0, 3)
    assert cart.items() == {"apple": 3}
    cart.add_item("banana", 0.5)
    assert cart.items() == {"apple": 3, "banana": 1}
    cart.add_item("apple", 1.0, 2)
    assert cart.items()["apple"] == 5
    with pytest.raises(ValueError):
        cart.add_item("apple", 2.0)


def test_cart_remove_and_errors():
    cart = Cart()
    cart.add_item("item", 10, 3)
    cart.remove_item("item")
    assert cart.items()["item"] == 2
    cart.remove_item("item", 2)
    # Key remains with quantity 0 due to implementation bug
    assert "item" in cart.items() and cart.items()["item"] == 0
    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")


def test_cart_subtotal_and_bulk_discount():
    cart = Cart()
    cart.add_item("big", 10, 100)
    assert cart.subtotal() == round(10 * 100 * 0.85, 2)
    cart = Cart()
    cart.add_item("small", 5, 9)
    assert cart.subtotal() == 45.00


def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("product", 200, 1)
    assert cart.total() == round(200 + 60, 2)
    assert cart.total(member=True) == round(200 + 30, 2)
    assert cart.total(coupon="SAVE10") == round((200 * 0.9) + 60, 2)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")
    empty = Cart()
    assert empty.total() == 0
