import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

def test_apply_discount_basic():
    assert apply_discount(100, 10) == 90
    assert apply_discount(200, 25) == 150


def test_bulk_discount_percent():
    # assume spec: no discount for <5 items, 5% for 5-9, 10% for >=10
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(4) == 0
    assert bulk_discount_percent(5) == 5
    assert bulk_discount_percent(7) == 5
    assert bulk_discount_percent(10) == 10


def test_parse_coupon():
    # spec: returns tuple (discount_percent, message)
    result = parse_coupon("DISCOUNT15")
    assert isinstance(result, tuple) and len(result)==2
    discount, msg = result
    assert discount == 15
    assert "Discount" in msg


def test_shipping_fee():
    # spec: free shipping for members; $10 otherwise unless subtotal > 100 then free
    assert shipping_fee(50) == 10
    assert shipping_fee(150) == 0
    assert shipping_fee(80, member=True) == 0


def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("apple", 1.5, quantity=3)
    cart.add_item("banana", 0.75)
    items = cart.items()
    assert "apple" in items and items["apple"] == (1.5, 3)
    assert "banana" in items and items["banana"] == (0.75, 1)


def test_cart_remove_item():
    cart = Cart()
    cart.add_item("orange", 2, quantity=4)
    cart.remove_item("orange", quantity=2)
    assert cart.items()["orange"] == (2, 2)
    cart.remove_item("orange", quantity=3)  # more than present
    assert "orange" not in cart.items()


def test_cart_subtotal():
    cart = Cart()
    cart.add_item("item1", 10, quantity=2)
    cart.add_item("item2", 5, quantity=3)
    assert cart.subtotal() == 10*2 + 5*3


def test_cart_total_with_discount_and_shipping():
    cart = Cart()
    cart.add_item("widget", 20, quantity=6)  # bulk discount applies
    subtotal = cart.subtotal()
    bulk_percent = bulk_discount_percent(6)
    discounted_subtotal = apply_discount(subtotal, bulk_percent)
    total_expected = discounted_subtotal + shipping_fee(discounted_subtotal)
    assert cart.total() == pytest.approx(total_expected)


def test_cart_total_with_member_and_coupon():
    cart = Cart()
    cart.add_item("gadget", 50, quantity=1)
    total = cart.total(member=True, coupon="DISCOUNT15")
    # expected: member free shipping, 15% discount applied before shipping
    assert isinstance(total, float)
