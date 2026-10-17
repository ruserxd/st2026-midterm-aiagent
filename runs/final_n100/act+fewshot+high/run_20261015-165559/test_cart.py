import pytest
import cart

def test_apply_discount_negative_price_raises():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (20, 25, 15.0),
    (19, 0, 19.0),
    (10, 100, 0.0)
])
def test_apply_discount_calculation(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-1, 10), (20, -5), (20, 105)
])
def test_apply_discount_invalid_percent_or_price_raises(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (50, 10),
    (51, 10),  # >=50
    (100, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save10", 10),          # case-insensitive expected per spec
    ("   SAVE20  ", 20)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV",            # too short
    "SAVE0",          # percent out of range <1
    "SAVE51",         # >50
    "ABC10",
    None,
    123
])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,expected_fee", [
    (999, 60),
    (1000, 0)
])
def test_shipping_fee_non_member(subtotal, expected_fee):
    assert cart.shipping_fee(subtotal) == expected_fee

@pytest.mark.parametrize("subtotal,expected_fee", [
    (999, 30),   # half for member
    (1000, 0)
])
def test_shipping_fee_member(subtotal, expected_fee):
    assert cart.shipping_fee(subtotal, member=True) == expected_fee

def test_shipping_fee_negative_raises():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Cart class tests
@pytest.fixture

def empty_cart():
    return cart.Cart()


def test_cart_add_item_success_and_errors(empty_cart):
    c = empty_cart
    c.add_item('apple', 1.5, quantity=3)
    assert c.items() == {'apple': 3}
    # Negative unit price
    with pytest.raises(ValueError):
        c.add_item('banana', -2.0, quantity=1)
    # Non-positive quantity
    with pytest.raises(ValueError):
        c.add_item('banana', 2.0, quantity=0)


def test_cart_add_same_item_increases_qty_and_error_if_different_price(empty_cart):
    c = empty_cart
    c.add_item('apple', 1.5, quantity=3)
    c.add_item('apple', 1.5, quantity=2)
    assert c.items() == {'apple': 5}
    with pytest.raises(ValueError):
        c.add_item('apple', 2.0, quantity=1)


def test_cart_remove_item_success_and_removal_when_zero(empty_cart):
    c = empty_cart
    c.add_item('banana', 2.0, quantity=4)
    c.remove_item('banana', quantity=2)
    assert c.items() == {'banana': 2}
    # Remove remaining quantity
    c.remove_item('banana', quantity=2)
    assert c.items() == {}
    # Removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item('cherry', quantity=1)


def test_cart_items_returns_copy(empty_cart):
    c = empty_cart
    c.add_item('apple', 3.0, quantity=2)
    items_dict = c.items()
    assert items_dict == {'apple': 2}
    # Modify returned dict should not affect cart
    items_dict['apple'] = 10
    assert c.items() == {'apple': 2}


def test_cart_subtotal_no_discount(empty_cart):
    c = empty_cart
    c.add_item('widget', 5.0, quantity=2)
    assert c.subtotal() == 10.0


def test_cart_subtotal_with_bulk_discount_and_rounding(empty_cart):
    c = empty_cart
    # Item that triggers bulk discount
    c.add_item('gadget', 10.01, quantity=3)  # line_total=30.03, 10% discount -> 27.027 -> round 27.03
    assert c.subtotal() == 27.03


def test_cart_subtotal_multiple_items(empty_cart):
    c = empty_cart
    c.add_item('item1', 5.0, quantity=2)   # 10 no discount
    c.add_item('item2', 3.0, quantity=12)  # 36, 10% discount -> 32.4
    assert c.subtotal() == 42.4


def test_cart_total_without_coupon_and_member(empty_cart):
    c = empty_cart
    c.add_item('apple', 5.0, quantity=2)
    assert c.total(member=False) == 70.0   # subtotal 10 + shipping 60
    assert c.total(member=True) == 40.0    # subtotal 10 + shipping 30


def test_cart_total_with_coupon_not_crossing_threshold(empty_cart):
    c = empty_cart
    c.add_item('apple', 5.0, quantity=4)   # subtotal 20
    total = c.total(coupon='SAVE10')
    expected_amount_after_discount = cart.apply_discount(20, 10)  # 18.0
    expected_shipping = cart.shipping_fee(expected_amount_after_discount)
    assert total == round(expected_amount_after_discount + expected_shipping, 2)


def test_cart_total_with_coupon_crossing_threshold(empty_cart):
    c = empty_cart
    # Create subtotal >1000
    c.add_item('expensive', 200.0, quantity=6)  # 1200
    total = c.total(coupon='SAVE50')
    discounted_amount = cart.apply_discount(1200, 50)   # 600
    expected_shipping = cart.shipping_fee(discounted_amount)
    expected_total = round(discounted_amount + expected_shipping, 2)
    assert total == expected_total


def test_cart_total_invalid_coupon_raises(empty_cart):
    c = empty_cart
    c.add_item('apple', 5.0, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon='SAVE70')


def test_cart_total_empty_cart_returns_zero():
    c = cart.Cart()
    assert c.total() == 0
