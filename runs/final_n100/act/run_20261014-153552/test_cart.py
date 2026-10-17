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
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (20, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVEB10", "HELLO", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------
@pytest.fixture
def cart():
    return Cart()

def test_cart_initial(cart):
    assert cart.items() == []
    assert cart.subtotal() == 0
    assert cart.total() == 0

def test_add_and_remove_items(cart):
    cart.add_item("apple", unit_price=100, quantity=2)
    cart.add_item("banana", 50)
    assert len(cart.items()) == 2
    # subtotal = 2*100 + 1*50 = 250
    assert cart.subtotal() == 250
    # total without coupon or member
    expected = round(250 + shipping_fee(250), 2)  # 60 shipping
    assert cart.total() == expected

    # remove one apple
    cart.remove_item("apple")
    assert cart.subtotal() == 150  # one apple left + banana

    # removing more than present should not error but drop to zero quantity
    cart.remove_item("banana", quantity=5)
    assert len(cart.items()) == 1  # only apple remains

# Test coupon application on total

def test_cart_coupon(cart):
    cart.add_item("widget", 200, 3)  # subtotal 600
    # Apply 10% coupon
    expected_amount = apply_discount(600, 10)
    expected_total = round(expected_amount + shipping_fee(600), 2)
    assert cart.total(coupon="SAVE10") == expected_total

# Test member discount on shipping

def test_cart_member(cart):
    cart.add_item("gadget", 1000)
    # subtotal exactly 1000 -> free shipping regardless of membership
    assert cart.total(member=True) == round(1000 + shipping_fee(1000, True), 2)

# Test empty cart total is zero (no shipping)

def test_empty_cart_no_shipping(cart):
    assert cart.total() == 0
