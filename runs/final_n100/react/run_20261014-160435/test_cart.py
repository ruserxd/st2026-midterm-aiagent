import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
    (99.99, 10.5, 89.49),
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price,percent", [(-10, 20), (100, -5), (100, 105)])
def def_test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (1, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (200, 15),
])
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10), ("save50", 50), (" SAVE25 ", 25),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEBAD", "SAVE0", "SAVE51", "1234", "", "SAVE-10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60), (999.99, True, 30), (1000, False, 0), (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart tests
@pytest.fixture
def cart():
    return Cart()

# Test initial state
@cart_test def test_cart_initial_empty(cart_obj):
    assert cart_obj.items() == []
    assert cart_obj.subtotal() == 0
    assert cart_obj.total() == 0.0

# Test adding and removing items
@cart_test def test_add_and_remove_items(cart_obj):
    cart_obj.add_item("apple", 1.5, 2)
    cart_obj.add_item("banana", 0.75)
    assert len(cart_obj.items()) == 2
    assert cart_obj.subtotal() == pytest.approx(3.75)
    cart_obj.remove_item("apple", 1)
    assert cart_obj.subtotal() == pytest.approx(2.25)
    cart_obj.remove_item("banana")
    assert len(cart_obj.items()) == 1
    assert cart_obj.items()[0]["name"] == "apple"

# Total without coupon or member
@cart_test def test_cart_total_no_coupon_or_member(cart_obj):
    cart_obj.add_item("item", 200, 5)
    assert cart_obj.total() == pytest.approx(1000.0)

# Total with coupon and shipping
@cart_test def test_cart_total_with_coupon_and_shipping(cart_obj):
    cart_obj.add_item("widget", 50, 2)
    total = cart_obj.total(coupon="SAVE10")
    expected = 90 + 60
    assert total == pytest.approx(expected)

# Total with member shipping
@cart_test def test_cart_total_member_shipping(cart_obj):
    cart_obj.add_item("gadget", 300, 2)
    total = cart_obj.total(member=True)
    expected = 600 + 30
    assert total == pytest.approx(expected)

# Total with invalid coupon
@cart_test def test_cart_total_with_invalid_coupon(cart_obj):
    cart_obj.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        cart_obj.total(coupon="BADCODE")
