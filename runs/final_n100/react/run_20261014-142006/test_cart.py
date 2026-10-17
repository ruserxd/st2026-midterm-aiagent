import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100, 0, 100),
        (100, 100, 0),
        (150.5, 10, 135.45),  # round to 2 decimals
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [ -1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_breakpoints():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_basic():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe5") == 5

@ pytest.mark.parametrize(
    "code",
    ["",
     "save0",
     "save51",
     "discount10",
     " SAVE -5 ",
     "SAVE-5",
    ],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee_standard():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

@ pytest.mark.parametrize("subtotal", [ -1, -5])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# members get half fee
assert shipping_fee(500, member=True) == 30

# ---------- Cart class -----------------------------------------------------

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == {}
    cart.add_item("apple", 100, quantity=3)
    assert cart.items()["apple"] == (100, 3)
    # adding more of same item increases quantity
    cart.add_item("apple", 100, quantity=2)
    assert cart.items()["apple"] == (100, 5)
    cart.remove_item("apple", quantity=1)
    assert cart.items()["apple"] == (100, 4)
    # remove all quantities
    cart.remove_item("apple", quantity=4)
    assert "apple" not in cart.items()

@ pytest.mark.parametrize(
    "name, unit_price, quantity",
    [
        ("banana", -10, 1),
        ("pear", 20, -3),
    ],
)
def test_cart_invalid_add_raises(name, unit_price, quantity):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item(name, unit_price, quantity=quantity)

@ pytest.mark.parametrize(
    "name, quantity",
    [
        ("orange", 1),
        ("melon", 5),
    ],
)
def test_cart_remove_nonexistent_raises(name, quantity):
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item(name, quantity=quantity)

# subtotal calculation

def test_cart_subtotal():
    cart = Cart()
    cart.add_item("shirt", 200, 2)   # 400
    cart.add_item("jeans", 500, 1)   # 500
    assert cart.subtotal() == 900

# total calculation with discounts and coupons

def test_cart_total_with_bulk_and_coupon():
    cart = Cart()
    cart.add_item("pen", 50, quantity=10)  # bulk discount 5%
    subtotal = cart.subtotal()  # 500
    assert subtotal == 500
    total_no_coupons = cart.total(member=False)
    # apply bulk discount: 5% off -> 475.0
    assert total_no_coupons == pytest.approx(475.0)
    # member discount is separate; test coupon only
    total_coupon = cart.total(coupon="SAVE10")
    # bulk discount applied first, then coupon 10%
    assert total_coupon == pytest.approx(427.5)  # 475 - 47.5

# shipping fee inside total

def test_cart_total_shipping_fee():
    cart = Cart()
    cart.add_item("laptop", 1200)
    # subtotal > 1000, free shipping
    assert cart.total() == pytest.approx(1200)
    # member with small item should pay half fee
    cart = Cart()
    cart.add_item("book", 20)
    assert cart.total(member=True) == pytest.approx(20 + 30)  # 50.0

# coupon applied before shipping

def test_cart_total_coupon_and_shipping_order():
    cart = Cart()
    cart.add_item("phone", 800)
    # subtotal 800, not free shipping; member fee 30
    assert cart.total(member=False, coupon="SAVE10") == pytest.approx(720 + 60)  # 780.0
    # as member
    assert cart.total(member=True, coupon="SAVE10") == pytest.approx(720 + 30)   # 750.0
