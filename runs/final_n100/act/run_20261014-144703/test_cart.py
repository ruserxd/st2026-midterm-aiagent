import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- Discount helpers -----------------------------------------------------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result)

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 5), (20, -1), (30, 101)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ----- Bulk discount --------------------------------------------------------

@pytest.mark.parametrize(
    "quantity,percent",
    [
        (1, 0),
        (5, 0),
        (10, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, percent):
    assert bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----- Coupon parsing -------------------------------------------------------

valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    " SAVE5 ": 5,
    "SaVe50": 50,
}

@pytest.mark.parametrize("code,expected", valid_codes.items())
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVE51", "SAVE-5", "123", "SAVExx"]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- Shipping fee --------------------------------------------------------

@pytest.mark.parametrize(
    "subtotal,member,fee",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, fee):
    assert shipping_fee(subtotal, member=member) == fee

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Cart class -----------------------------------------------------------

cart = Cart()

def test_cart_initial_state():
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0

@pytest.mark.parametrize(
    "name,price,qty", [("apple", 100, 2), ("banana", 50, 5)],
)
def test_cart_add_item(name, price, qty):
    cart.add_item(name, price, qty)
    assert cart.items()[name] == qty

# Adding same item with same price increments quantity

def test_cart_add_same_item_increments():
    name = "orange"
    cart.add_item(name, 30, 1)
    cart.add_item(name, 30, 3)
    assert cart.items()[name] == 4

# Adding existing item with different price raises

def test_cart_add_conflicting_price():
    name = "grape"
    cart.add_item(name, 10, 1)
    with pytest.raises(ValueError):
        cart.add_item(name, 12, 2)

# Removing items decreases quantity or removes entirely

def test_cart_remove_items():
    name = "peach"
    cart.add_item(name, 20, 3)
    cart.remove_item(name, 1)
    assert cart.items()[name] == 2
    cart.remove_item(name, 2)  # should remove item entirely
    assert name not in cart.items()

# Removing non-existent raises KeyError

def test_cart_remove_missing():
    with pytest.raises(KeyError):
        cart.remove_item("nonexistent", 1)

# Subtotal calculation including bulk discount

def test_cart_subtotal_bulk_discount():
    c = Cart()
    c.add_item("widget", 50, 10)   # 5% discount
    c.add_item("gadget", 100, 51)  # 10% discount on gadget line
    expected_widget = 50 * 10 * 0.95  # 475
    expected_gadget = 100 * 51 * 0.90  # 4590
    assert c.subtotal() == pytest.approx(round(expected_widget + expected_gadget, 2))

# Total with coupon and shipping fee (non-member)

def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("item", 200, 5)  # no bulk discount
    subtotal = 200 * 5
    discounted = apply_discount(subtotal, 10)  # coupon SAVE10
    fee = shipping_fee(discounted)
    total_expected = round(discounted + fee, 2)
    assert c.total(coupon="SAVE10") == pytest.approx(total_expected)

# Total for empty cart returns 0 (no shipping)

def test_cart_total_empty_no_shipping():
    e = Cart()
    assert e.total() == 0

# Coupon invalid raises ValueError in total

def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("test", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
