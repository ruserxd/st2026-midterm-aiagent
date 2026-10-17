import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Test apply_discount

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0
    assert apply_discount(123.456, 10) == round(123.456 * 0.9, 2)

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 50)

def test_apply_discount_invalid_percent():
    for bad in [-10, 101]:
        with pytest.raises(ValueError):
            apply_discount(100, bad)

# Test bulk_discount_percent

def test_bulk_discount_percent():
    assert bulk_discount_percent(0) == 0.0
    assert bulk_discount_percent(5) == 0.0
    assert bulk_discount_percent(10) == 2.0
    assert bulk_discount_percent(20) == 5.0
    assert bulk_discount_percent(25) == 7.5

# Test parse_coupon

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == ("percentage", 10)
    assert parse_coupon("DISCOUNT15") == ("discount", 15)
    assert parse_coupon("FREESHIP") == ("free_shipping", None)


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        parse_coupon("invalid_code")

# Test shipping_fee

def test_shipping_fee_member():
    assert shipping_fee(0) == 5.0
    assert shipping_fee(50) == 5.0
    assert shipping_fee(101) == 10.0

    # member discounts
    assert shipping_fee(100, member=True) == 0.0
    assert shipping_fee(200, member=True) == 0.0

# Test Cart functionality

def test_cart_add_and_items():
    c = Cart()
    c.add_item("apple", 1.5, quantity=2)
    c.add_item("banana", 0.75)
    items = c.items()
    assert len(items) == 2
    names = {item[0] for item in items}
    assert names == {"apple", "banana"}


def test_cart_subtotal_and_total():
    c = Cart()
    c.add_item("toy", 10.0, quantity=3)  # subtotal 30
    assert c.subtotal() == 30.0
    # no coupon or member
    assert c.total() == 35.0  # subtotal + shipping 5
    # member discount applies to total? expects free shipping if subtotal>100? not sure.
    c.add_item("expensive", 200.0)
    # now subtotal 230, shipping fee should be 10 for non-member, 0 for member.
    assert c.total(member=True) == 240.0


def test_cart_remove():
    c = Cart()
    c.add_item("pen", 2.0, quantity=5)
    c.remove_item("pen", quantity=3)
    assert len(c.items()) == 1
    name, price, qty = c.items()[0]
    assert qty == 2
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")
