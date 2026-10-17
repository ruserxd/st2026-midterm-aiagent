import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper functions for expected calculations ----------

def expect_apply(price, percent):
    return round(price * (1 - percent / 100), 2)

# ---------- Tests for standalone functions ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),            # example from spec
        (100, 0, 100.0),             # no discount
        (50, 100, 0.0),              # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

# Value errors for negative price or invalid percent
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),       # below threshold
        (10, 5),      # first tier
        (49, 5),
        (50, 10),     # second tier
        (99, 10),
        (100, 15),    # third tier
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE25 ", 25),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "INVALID", "", "SAVExx"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (800, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

# Helper to create a cart with some items

def make_cart():
    c = Cart()
    c.add_item("apple", 100, 5)   # subtotal: 500, bulk discount 5% -> 475.0
    c.add_item("banana", 200, 12) # subtotal: 2400, bulk discount 10% -> 2160.0
    return c

def test_cart_add_and_items():
    c = Cart()
    c.add_item("widget", 50, 3)
    assert c.items() == {"widget": 3}
    # adding same item increases quantity
    c.add_item("widget", 50, 2)
    assert c.items() == {"widget": 5}
    with pytest.raises(ValueError):
        c.add_item("widget", 60)  # price mismatch

@pytest.mark.parametrize(
    "quantity", [0, -1, 3.7])
def test_cart_add_invalid(quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("gadget", 30, quantity)

# remove_item tests

def test_cart_remove():
    c = Cart()
    c.add_item("itemA", 10, 4)
    c.remove_item("itemA", 2)
    assert c.items() == {"itemA": 2}
    # removing remaining quantity removes item
    c.remove_item("itemA", 2)
    assert c.items() == {}

def test_cart_remove_not_present():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# subtotal calculations with bulk discounts

def test_cart_subtotal_with_bulk_discount():
    c = make_cart()
    # apple: 5 * 100 = 500, discount 5% => 475.0
    # banana: 12 * 200 = 2400, discount 10% => 2160.0
    expected = round(475.0 + 2160.0, 2)
    assert c.subtotal() == expected

# subtotal empty cart

def test_cart_empty_subtotal():
    assert Cart().subtotal() == 0

# total without coupon or member

def test_cart_total_no_coupon_member():
    c = make_cart()
    # subtotal as above
    sub = c.subtotal()
    shipping = shipping_fee(sub)
    expected = round(sub + shipping, 2)
    assert c.total() == expected

# total with member discount (shipping half)

def test_cart_total_member():
    c = make_cart()
    sub = c.subtotal()
    shipping = shipping_fee(sub, member=True)
    expected = round(sub + shipping, 2)
    assert c.total(member=True) == expected

# total with coupon discount

def test_cart_total_with_coupon():
    c = make_cart()
    sub = c.subtotal()
    # apply a 20% coupon
    discounted = round(sub * (1 - 0.2), 2)
    shipping = shipping_fee(discounted)
    expected = round(discounted + shipping, 2)
    assert c.total(coupon="SAVE20") == expected

# total with invalid coupon raises ValueError

def test_cart_total_invalid_coupon():
    c = make_cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# empty cart costs zero, no shipping

def test_empty_cart_total():
    assert Cart().total() == 0
