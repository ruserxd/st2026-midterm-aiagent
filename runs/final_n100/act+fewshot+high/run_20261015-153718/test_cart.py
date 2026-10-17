import pytest
import cart


def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,expected", [
    (100, 20, 80.0),
    (99.99, 20, 79.99),   # 99.99 * 0.8 = 79.992 -> round to 2 decimals
    (10, 100, 0.0),
    (10, 0, 10.0),
])
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-1, 20),   # negative price
    (100, -5),  # percent too low
    (100, 105), # percent too high
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


def test_bulk_discount_percent_basic():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty,expected", [
    (9, 0), (10, 5), (49, 5),
    (50, 10), (99, 10), (100, 15)
])
def test_bulk_discount_percent_edges(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, -10])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)


@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEX",
    "SAVE0",
    "SAVE51",
    "",
    "   ",
    "save10abc",
    "SaVe100",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1200.5, True, 0),
    (999.99, False, 60),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)


# Cart tests

def test_cart_add_item_basic():
    c = cart.Cart()
    c.add_item('apple', 0.99, quantity=1)
    assert c.items() == {'apple': 1}


def test_cart_add_existing_same_price_increases_quantity():
    c = cart.Cart()
    c.add_item('banana', 0.5, quantity=2)
    c.add_item('banana', 0.5, quantity=3)
    assert c.items() == {'banana': 5}


def test_cart_add_different_unit_price_raises():
    c = cart.Cart()
    c.add_item('orange', 1.0, quantity=1)
    with pytest.raises(ValueError):
        c.add_item('orange', 1.2, quantity=1)

@pytest.mark.parametrize("unit_price", [-1, -0.01])
def test_cart_add_negative_unit_price(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('pear', unit_price, quantity=1)

@pytest.mark.parametrize("quantity", [0, -5, -1])
def test_cart_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('grape', 2.0, quantity=quantity)


def test_cart_remove_reduce_quantity():
    c = cart.Cart()
    c.add_item('apple', 1.0, quantity=5)
    c.remove_item('apple', quantity=3)
    assert c.items() == {'apple': 2}


def test_cart_remove_to_zero_removes_item():
    c = cart.Cart()
    c.add_item('banana', 1.0, quantity=2)
    c.remove_item('banana', quantity=2)
    assert 'banana' not in c.items()


def test_cart_remove_more_than_exists_removes_item():
    c = cart.Cart()
    c.add_item('orange', 1.0, quantity=2)
    c.remove_item('orange', quantity=5)  # should remove completely without error
    assert 'orange' not in c.items()


def test_cart_remove_nonexistent_raises_key_error():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('pear', quantity=1)


def test_cart_items_returns_copy_and_not_reference():
    c = cart.Cart()
    c.add_item('apple', 0.5, quantity=3)
    items_ref = c.items()
    items_ref['apple'] = 10
    assert c.items()['apple'] == 3  # original unchanged


def test_cart_subtotal_no_discount_single_item():
    c = cart.Cart()
    c.add_item('single', 2.0, quantity=1)
    assert c.subtotal() == 2.0


def test_cart_subtotal_multiple_discounts():
    c = cart.Cart()
    # item A: qty 10 => discount 5%
    c.add_item('A', 0.99, quantity=10)   # base total 9.90, discounted 9.405
    # item B: qty 5 no discount
    c.add_item('B', 1.12, quantity=5)    # 5.6
    expected = round(9.405 + 5.6, 2)
    assert c.subtotal() == expected


def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0


def test_cart_total_without_coupon_non_member_shipping():
    c = cart.Cart()
    # Add items to get subtotal after bulk discount
    c.add_item('small', 50, quantity=10)  # qty=10 => discount 5%
    expected_subtotal = round(50 * 10 * 0.95, 2)
    assert c.subtotal() == expected_subtotal
    # no coupon, non-member => shipping 60 (subtotal <1000)
    expected_total = round(expected_subtotal + 60, 2)
    assert c.total() == expected_total


def test_cart_total_with_coupon_member_shipping():
    c = cart.Cart()
    c.add_item('small', 50, quantity=10)   # discounted subtotal 475.0
    coupon_percent = cart.parse_coupon('SAVE10')
    amount_after_coupon = round(c.subtotal() * (100 - coupon_percent) / 100, 2)
    shipping_fee_member = cart.shipping_fee(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + shipping_fee_member, 2)
    assert c.total(member=True, coupon='SAVE10') == expected_total


def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('item', 1.0, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')


def test_cart_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon='SAVE10') == 0


def test_cart_total_subtotal_above_1000_coupon_below_1000_shipping_applied_non_member():
    c = cart.Cart()
    c.add_item('expensive', 1100, quantity=1)
    # subtotal before coupon
    assert c.subtotal() == 1100.0
    amount_after_coupon = round(c.subtotal() * (100 - 20) / 100, 2)  # SAVE20 -> 20% off
    shipping_fee_non_member = cart.shipping_fee(amount_after_coupon, member=False)
    expected_total = round(amount_after_coupon + shipping_fee_non_member, 2)
    assert c.total(coupon='SAVE20') == expected_total


def test_cart_total_subtotal_above_1000_coupon_below_1000_shipping_applied_member():
    c = cart.Cart()
    c.add_item('expensive', 1100, quantity=1)
    amount_after_coupon = round(c.subtotal() * (100 - 20) / 100, 2)
    shipping_fee_member = cart.shipping_fee(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + shipping_fee_member, 2)
    assert c.total(member=True, coupon='SAVE20') == expected_total
