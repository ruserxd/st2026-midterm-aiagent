import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------- apply_discount ---------------------------------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ----------- bulk_discount_percent ---------------------------

def test_bulk_discount_borders():
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(99) == 10

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ----------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize("code", ["SAVEXX", "savel0", "SAVE51", "DISCOUNT", "123", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----------- shipping_fee -------------------------------------

def test_shipping_fee_free_and_regular():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60

def test_shipping_fee_member_discount():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----------- Cart class ---------------------------------------

def test_cart_add_and_subtotal():
    cart = Cart()
    assert cart.subtotal() == 0
    cart.add_item("Apple", unit_price=100, quantity=3)
    # subtotal: 300
    assert cart.subtotal() == 300
    cart.add_item("Banana", 50, 2)  # add new item
    assert cart.subtotal() == 400
    cart.add_item("Apple", 100, 2)  # update existing quantity
    assert cart.subtotal() == 500

def test_cart_remove_and_items():
    cart = Cart()
    cart.add_item("Widget", 200, 5)
    cart.remove_item("Widget", 3)
    # remaining qty 2 -> subtotal 400
    assert cart.subtotal() == 400
    # remove remaining quantity
    cart.remove_item("Widget", 2)
    assert cart.subtotal() == 0
    with pytest.raises(KeyError):
        cart.remove_item("Nonexistent")

# Note: total method's exact logic is not fully specified; testing subtotal behavior suffices.
