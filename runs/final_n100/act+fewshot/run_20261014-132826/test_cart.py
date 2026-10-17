import pytest
import cart

UNIT_PRICE = 2.5
QUANTITY_A = 3
ITEM_NAME = "apple"

# ---------- apply_discount -------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon --------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE5 ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVEXY", "SAVE0", "SAVE51", "", "10SAVE"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200, False, 0),
        (1200, True, 0),
        (800, False, 60),
        (800, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -----------------------------------------------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 60.0

c = cart.Cart()
c.add_item(ITEM_NAME, unit_price=UNIT_PRICE, quantity=QUANTITY_A)
assert c.items() == {ITEM_NAME: QUANTITY_A}
assert c.subtotal() == UNIT_PRICE * QUANTITY_A

c.add_item(ITEM_NAME, unit_price=UNIT_PRICE, quantity=2)
assert c.items() == {ITEM_NAME: 5}
assert c.subtotal() == UNIT_PRICE * 5

c.add_item("banana", unit_price=1.0, quantity=4)
assert c.items() == {ITEM_NAME: 5, "banana": 4}
assert c.subtotal() == UNIT_PRICE * 5 + 4.0

c.remove_item(ITEM_NAME, quantity=3)
assert c.items() == {ITEM_NAME: 2, "banana": 4}
c.remove_item("banana")
assert c.items() == {ITEM_NAME: 2, "banana": 3}

# Removing more than existing does not raise in this implementation
c.remove_item(ITEM_NAME, quantity=10)
assert c.items() == {"banana": 3}

# Removing non-existent item raises KeyError
with pytest.raises(KeyError):
    c.remove_item("cherry")

c = cart.Cart()
c.add_item("item", unit_price=100, quantity=12)  # bulk discount applied to subtotal
assert c.subtotal() == 1140.0
assert c.total(member=False, coupon=None) == 1140.0
c.add_item("extra", unit_price=100, quantity=1)
assert c.subtotal() == 1240.0
expected_total = 1240.0 * 0.90
assert c.total(member=False, coupon="SAVE10") == pytest.approx(expected_total)

c = cart.Cart()
# Invalid coupon is ignored; total should act as no coupon
assert c.total(coupon="INVALID") == 60.0
