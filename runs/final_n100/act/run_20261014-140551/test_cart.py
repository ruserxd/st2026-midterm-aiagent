import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),   # example from spec
        (100, 0, 100.0),      # no discount
        (50.5, 10, 45.45),    # rounding check
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == result

# boundary conditions for errors
@pytest.mark.parametrize(
    "price,percent",
    [
        (-1, 10),              # negative price
        (100, -5),             # negative percent
        (100, 105),            # percent > 100
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# error for non‑positive quantity
@pytest.mark.parametrize("quantity", [0, -10])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),            # case‑insensitive
        (" SAVE30 ", 30),           # whitespace stripped
        ("SaVe50", 50),            # upper boundary
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEX",
    "SAVE0",
    "SAVE51",
    "INVALID",
    "10SAVE",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200, False, 0),            # free for any member
        (999.99, False, 60),         # regular fee
        (500, True, 30),             # member half fee
        (1000, True, 0),             # boundary, still free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_basic_operations():
    cart = Cart()
    # initially empty
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 60   # subtotal 0, no member, no coupon => shipping 60

    # add items
    cart.add_item("apple", 2.5, quantity=4)
    cart.add_item("banana", 1.0)      # default quantity 1
    assert cart.items() == {
        "apple": (2.5, 4),
        "banana": (1.0, 1),
    }
    assert cart.subtotal() == 2.5 * 4 + 1.0

    # test bulk discount applied via coupon? no; just ensure total uses shipping
    subtotal = 10.0
    assert cart.total(member=True) == subtotal + 30   # member fee 30 (since subtotal <1000)

    # remove item partially
    cart.remove_item("apple", quantity=2)
    assert cart.items()["apple"] == (2.5, 2)

    # removing more than present removes the item entirely
    cart.remove_item("banana")   # default quantity 1 removal
    assert "banana" not in cart.items()

    # test coupon discount via total
    cart.add_item("item", 100, quantity=10)  # subtotal 1000 -> free shipping
    assert cart.total(coupon="SAVE5") == 1000 * 0.95 + 0

    # test invalid coupon raises ValueError in total
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ---------- Cart edge cases ----------

def test_cart_negative_prices_and_quantities():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", -5, 1)
    with pytest.raises(ValueError):
        cart.add_item("bad2", 5, quantity=-3)

# Test that remove non‑existing item does nothing or raises? Implementation expected to ignore.
def test_cart_remove_nonexistent():
    cart = Cart()
    # no error should be raised
    cart.remove_item("ghost")
    assert cart.items() == {}
