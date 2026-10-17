import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Discount functions ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0
    assert apply_discount(99.99, 10) == round(99.99 * 0.90, 2)

@pytest.mark.parametrize("price, percent", [(-1, 20), (50, -5), (30, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Bulk discount ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(250) == 15

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Coupon parsing ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save50") == 50
    assert parse_coupon(" SAVE20 ") == 20

@pytest.mark.parametrize(
    "code",
    ["", "SAVEx", "SAVE0", "SAVE51", "abc10", "SA VE10", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Shipping fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0
    assert shipping_fee(50, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0

def test_add_and_items():
    cart = Cart()
    cart.add_item("apple", 1.5, quantity=3)
    cart.add_item("banana", 2.0, quantity=2)
    assert cart.items() == {"apple": 3, "banana": 2}

    cart.add_item("apple", 1.5, quantity=2)
    assert cart.items()["apple"] == 5

    with pytest.raises(ValueError):
        cart.add_item("apple", 1.6, quantity=1)

    with pytest.raises(ValueError):
        cart.add_item("orange", -1.0)

    with pytest.raises(ValueError):
        cart.add_item("orange", 1.0, quantity=0)

def test_remove_item():
    cart = Cart()
    cart.add_item("item", 10.0, quantity=5)
    cart.remove_item("item", quantity=2)
    assert cart.items()["item"] == 3

    cart.remove_item("item", quantity=3)
    assert "item" not in cart.items()

    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")

def test_subtotal_with_bulk_discount():
    cart = Cart()
    cart.add_item("widget", 99.99, quantity=12)
    expected_line_total = round(99.99 * 12 * 0.95, 2)
    assert cart.subtotal() == expected_line_total

    cart.add_item("gadget", 20.0, quantity=55)
    gadget_total = round(20.0 * 55 * 0.90, 2)
    assert cart.subtotal() == round(expected_line_total + gadget_total, 2)

def test_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("pen", 10.0, quantity=5)   # subtotal 50
    total_after_coupon = 40.0
    expected_total_nonmember = round(total_after_coupon + 60, 2)
    assert cart.total(member=False, coupon="SAVE20") == expected_total_nonmember

    expected_member_total = round(total_after_coupon + 30, 2)
    assert cart.total(member=True, coupon="SAVE20") == expected_member_total

def test_total_invalid_coupon():
    cart = Cart()
    cart.add_item("paper", 5.0)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

def test_total_empty_cart():
    cart = Cart()
    assert cart.total() == 0.0
