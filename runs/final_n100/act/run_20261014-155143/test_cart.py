import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------------------------------

def test_apply_discount_basic():
    # Example from specification
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
@ pytest.mark.parametrize("percent", [0])

def test_apply_discount_negative_price_raises(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@ pytest.mark.parametrize("percent", [-5, 105])
@ pytest.mark.parametrize("price", [10, 20])

def test_apply_discount_invalid_percent_raises(percent, price):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------------------------------

def test_bulk_discount_basic():
    # No discount for quantity <= 10
    assert bulk_discount_percent(0) == 0
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 0
    # 5% discount starting at 11 items
    assert bulk_discount_percent(11) == 5
    # Increase to 20 items
    assert bulk_discount_percent(20) == 5
    # 10% at 21+ items
    assert bulk_discount_percent(21) == 10
    assert bulk_discount_percent(30) == 10

# ---------- parse_coupon ----------------------------------

def test_parse_coupon_valid_codes():
    assert parse_coupon("SILVER") == 5
    assert parse_coupon("gold") == 10
    # case-insensitive check
    assert parse_coupon("Platinum") == 15

@ pytest.mark.parametrize("code", ["bronze", "silver silver", ""])

def test_parse_coupon_invalid_codes(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------------------------------

def test_shipping_fee_member_nonmember():
    # non-member, subtotal < 50 -> 10
    assert shipping_fee(30) == 10
    # non-member, subtotal exactly 50 -> free
    assert shipping_fee(50) == 0
    # member, always free
    assert shipping_fee(20, member=True) == 0
    assert shipping_fee(100, member=True) == 0

# ---------- Cart class ----------------------------------

@pytest.fixture
def cart_obj():
    return Cart()


def test_add_and_items(cart_obj):
    cart_obj.add_item("apple", unit_price=1.5)
    assert cart_obj.items() == [({"name": "apple", "unit_price": 1.5, "quantity": 1},)]

    # Add same item increases quantity
    cart_obj.add_item("apple", unit_price=1.5, quantity=2)
    assert cart_obj.items()[0][0]['quantity'] == 3

    cart_obj.add_item("banana", unit_price=2.0, quantity=4)
    names = [entry[0]['name'] for entry in cart_obj.items()]
    assert set(names) == {"apple", "banana"}


def test_remove_and_items(cart_obj):
    cart_obj.add_item("orange", 1.0, quantity=3)
    # remove part of quantity
    cart_obj.remove_item("orange", quantity=2)
    assert cart_obj.items()[0][0]['quantity'] == 1
    # removing remaining removes item entirely
    cart_obj.remove_item("orange")
    assert cart_obj.items() == []


def test_subtotal(cart_obj):
    cart_obj.add_item("itemA", 2.5, quantity=2)  # 5.0
    cart_obj.add_item("itemB", 1.0, quantity=4)  # 4.0
    assert cart_obj.subtotal() == pytest.approx(9.0)


def test_total_without_discounts(cart_obj):
    cart_obj.add_item("foo", 10, quantity=2)  # subtotal 20
    # member false, no coupon, free shipping
    assert cart_obj.total() == 20.0


def test_total_with_coupon_and_shipping(cart_obj):
    cart_obj.add_item("bar", 30)
    # subtotal 30 <50 -> shipping 10
    assert cart_obj.total(coupon="SILVER") == pytest.approx(30 * 0.95 + 10)


def test_total_bulk_discount(cart_obj):
    cart_obj.add_item("bulk", 1, quantity=25)  # subtotal 25
    # bulk discount 10% => 22.5, shipping free for non-member because subtotal >=50? but subtotal <50 so shipping 10
    expected = 22.5 + 10
    assert cart_obj.total() == pytest.approx(expected)
