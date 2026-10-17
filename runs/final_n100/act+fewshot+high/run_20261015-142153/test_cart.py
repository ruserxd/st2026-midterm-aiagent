import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 50) == 50.0
    assert cart.apply_discount(123.45, 20) == round(123.45 * 0.8, 2)
    assert cart.apply_discount(10, 33) == round(10 * (100 - 33) / 100, 2)

def test_apply_discount_invalid_inputs():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 101)

@pytest.mark.parametrize("quantity,expected", [
    (1, 0), (9, 0),
    (10, 5), (15, 5), (49, 5),
    (50, 10), (51, 10), (99, 10),
    (100, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe30   ", 30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["BAD", "SAVE0", "SAVE51"])
def test_parse_coupon_invalid_code(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_parse_coupon_non_string():
    with pytest.raises(ValueError):
        cart.parse_coupon(None)

@pytest.mark.parametrize(
    "subtotal,member,expected_fee",
    [
        (999, False, 60),
        (999, True, 30),
        (1000, False, 0),
        (1000, True, 0),
        (2000, False, 0)
    ]
)
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member) == expected_fee

def test_shipping_fee_negative_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1, False)

def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert not c.items()

def test_cart_add_item_basic_and_updates():
    c = cart.Cart()
    c.add_item('apple', 1.5, 3)
    assert c.items() == {'apple': 3}
    c.add_item('apple', 1.5, 2)
    assert c.items()['apple'] == 5

def test_cart_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item('orange', 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item('orange', 3.0, 1)

def test_cart_add_item_negative_unit_price_raises():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('bad', -5, 1)

def test_cart_add_item_invalid_quantity():
    c = cart.Cart()
    for qty in [0, -1]:
        with pytest.raises(ValueError):
            c.add_item('badqty', 1.0, qty)
    with pytest.raises(ValueError):
        c.add_item('badqty2', 1.0, 'two')

def test_cart_add_item_zero_unit_price_allowed():
    c = cart.Cart()
    c.add_item('free', 0.0, 5)
    assert c.items()['free'] == 5

def test_cart_remove_item_updates_quantity():
    c = cart.Cart()
    c.add_item('apple', 1.0, 3)
    c.remove_item('apple', 2)
    assert c.items()['apple'] == 1

def test_cart_remove_item_removes_when_zero():
    c = cart.Cart()
    c.add_item('apple', 1.0, 3)
    c.remove_item('apple', 3)  # should remove item
    assert 'apple' not in c.items()

def test_cart_remove_more_than_remaining_removes():
    c = cart.Cart()
    c.add_item('banana', 1.0, 2)
    c.remove_item('banana', 5)  # should remove item
    assert 'banana' not in c.items()

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('ghost')

def test_cart_subtotal_basic():
    c = cart.Cart()
    c.add_item('item1', 10.0, 5)   # quantity <10 => no discount
    c.add_item('item2', 20.0, 51)  # >=51 => 10% discount
    expected_total = round(50 + 918, 2)
    assert c.subtotal() == expected_total

def test_cart_subtotal_empty():
    assert cart.Cart().subtotal() == 0

def test_cart_total_empty_returns_zero():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon_member_flags():
    c = cart.Cart()
    c.add_item('cheap', 10.0, 2) # subtotal 20
    # non-member
    assert c.total(member=False) == 80
    # member
    assert c.total(member=True) == 50

def test_cart_total_with_coupon_below_threshold():
    c = cart.Cart()
    c.add_item('cheap', 10.0, 2) # subtotal 20
    assert c.total(member=False,coupon='SAVE10') == 78
    assert c.total(member=True,coupon='SAVE10') == 48

def test_cart_total_no_coupon_with_free_shipping():
    c = cart.Cart()
    c.add_item('expensive', 200.0, 6)  # subtotal 1200 > 1000
    assert c.total() == 1200

def test_cart_total_with_coupon_cross_threshold():
    c = cart.Cart()
    c.add_item('expensive', 200.0, 6)  # subtotal 1200 > 1000
    # non-member
    assert c.total(member=False, coupon='SAVE20') == 1020
    # member
    assert c.total(member=True, coupon='SAVE20') == 990

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('item', 10.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
