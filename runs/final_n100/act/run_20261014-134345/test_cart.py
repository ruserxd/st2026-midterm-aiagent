import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- apply_discount -------------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

# Boundary cases for percent limits
@pytest.mark.parametrize("price,percent", [
    (10, -1),          # below 0
    (10, 101),         # above 100
])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@pytest.mark.parametrize("price", [-5, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

# ----- bulk_discount_percent -----------------------------------------------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----- parse_coupon ---------------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save25 ") == 25
    assert parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "abc", "123", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- shipping_fee --------------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Cart ---------------------------------------------------------------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 2.5)
    expected = {"apple": (1.0, 3), "banana": (2.5, 1)}
    assert c.items() == expected


def test_cart_remove_and_subtotal():
    c = Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 2)   # should leave 3
    assert c.items()["apple"] == (1.0, 3)
    assert c.subtotal() == 3 * 1.0

    # removing more than present should remove the item completely
    c.remove_item("apple", 5)
    assert "apple" not in c.items()


def test_cart_total_with_member_and_coupon():
    c = Cart()
    c.add_item("widget", 100, 1)   # subtotal 100
    total_nonmember = c.total(member=False)
    # shipping 60 + subtotal 100 = 160
    assert total_nonmember == 160.0

    total_member = c.total(member=True)
    # shipping 30 + 100 = 130
    assert total_member == 130.0

    # apply a coupon SAVE20 (20% off before shipping?)
    total_with_coupon = c.total(member=False, coupon="SAVE20")
    # subtotal discounted: 100 * 0.8 = 80
    # shipping 60 => 140
    assert total_with_coupon == 140.0

# ----- Cart bulk discount on items (quantity) ----------------------------

def test_cart_bulk_discount_application():
    c = Cart()
    c.add_item("gadget", 10, 12)
    # quantity 12 triggers 5% bulk discount: price per unit becomes 9.5
    expected_total = 12 * 9.5 + shipping_fee(12*9.5, member=False)
    assert c.total() == expected_total
