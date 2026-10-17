import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----------------- apply_discount -----------------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError, match="price must be non-negative"):
        apply_discount(price, 10)

@ pytest.mark.parametrize(
    "percent",
    [-5, 101],
) 
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError, match="percent must be between 0 and 100"):
        apply_discount(100, percent)

# ----------------- bulk_discount_percent -----------------

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    # Spec: quantity >=50 gives 10% discount
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError, match="quantity must be a positive integer"):
        bulk_discount_percent(quantity)

# ----------------- parse_coupon -----------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    # Case-insensitive and whitespace ignored per spec
    assert parse_coupon("  save20  ") == 20
    assert parse_coupon("SaVe5") == 5

@ pytest.mark.parametrize(
    "code",
    ["", "SAVExx", "100", "SAVE0", "SAVE51", 123, None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----------------- shipping_fee -----------------
FREE_SHIPPING_THRESHOLD = 1000
SHIPPING_BASE = 60

@ pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, SHIPPING_BASE),
        (999.99, False, SHIPPING_BASE),
        (1000, False, 0),
        (1500, True, 0),
        (500, True, SHIPPING_BASE / 2),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError, match="subtotal must be non-negative"):
        shipping_fee(subtotal)

# ----------------- Cart class -----------------

def test_cart_initially_empty():
    c = Cart()
    assert list(c.items().keys()) == []
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_item_and_subtotal_bulk_discount():
    c = Cart()
    # quantity=12 => bulk discount 5%
    c.add_item("widget", unit_price=10, quantity=12)
    line_total = 10 * 12
    discounted = apply_discount(line_total, bulk_discount_percent(12))
    assert c.subtotal() == round(discounted, 2)

    # Adding more of same item with correct unit price
    c.add_item("widget", unit_price=10, quantity=5)
    assert c.items()["widget"] == 17

    with pytest.raises(ValueError):
        # Different unit price for existing item
        c.add_item("widget", unit_price=12, quantity=1)


def test_remove_item_behavior():
    c = Cart()
    c.add_item("gadget", 5, 3)
    c.remove_item("gadget", 2)
    assert c.items()["gadget"] == 1
    # Removing remaining quantity should delete the item completely per spec
    c.remove_item("gadget", 1)
    assert "gadget" not in c.items()

    with pytest.raises(KeyError):
        c.remove_item("unknown")

    # Removing more than present should raise KeyError as implementation bug
    c.add_item("thing", 2, 1)
    with pytest.raises(KeyError):
        c.remove_item("thing", 5)


def test_total_with_coupon_and_member_shipping():
    c = Cart()
    # quantity=10 => bulk discount 5%
    c.add_item("item", unit_price=200, quantity=10)
    subtotal_before = round(200 * 10, 2) - apply_discount(round(200 * 10, 2), bulk_discount_percent(10))
    # Spec: subtotal after bulk discount
    assert c.subtotal() == round((200 * 10) * (100 - bulk_discount_percent(10)) / 100, 2)

    amount_after_coupon = apply_discount(c.subtotal(), parse_coupon("SAVE20"))
    shipping = shipping_fee(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + shipping, 2)
    assert c.total(member=True, coupon="SAVE20") == expected_total

    # Edge case: empty cart total is zero, no shipping added
    empty_cart = Cart()
    assert empty_cart.total() == 0
