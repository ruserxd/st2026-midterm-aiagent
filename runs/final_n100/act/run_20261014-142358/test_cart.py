import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- Helpers ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 12.5, round(123.45 * (1 - 0.125), 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 5), (50, -1), (70, 101)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.7],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
valid_cases = {
    'SAVE10': 10,
    'save20': 20,
    ' SaVe30 ': 30,
    'SAVE1': 1,
    'SAVE50': 50,
}

@pytest.mark.parametrize("code,expected", list(valid_cases.items()))
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = [
    'SAV10',   # missing E
    'SAVE0',   # below 1
    'SAVE51',  # above 50
    'SAVE-5',
    '10SAVE',
    '',
    '   ',
]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
        (400, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100.5],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart functionality ----------

def test_cart_basic_operations():
    c = Cart()
    # initial state
    assert list(c.items()) == []
    assert c.subtotal() == 0
    assert c.total() == 60  # 0 subtotal -> fee 60

    # add items
    c.add_item('apple', 1.5, 4)  # 6.0
    c.add_item('banana', 0.75)
    assert set(c.items()) == {('apple', 1.5, 4), ('banana', 0.75, 1)}
    assert c.subtotal() == 6.0 + 0.75

    # remove items
    c.remove_item('apple', 2)
    assert any(i[0] == 'apple' and i[2] == 2 for i in c.items())
    c.remove_item('banana')
    assert all(i[0] != 'banana' for i in c.items())

    # test totals with member flag and coupon
    c.add_item('widget', 100, 10)  # subtotal 1000 + previous items
    total = c.total(member=True, coupon='SAVE5')
    # compute expected: subtotal before discounts
    sub = c.subtotal()
    # bulk discount for widget (quantity=10 -> 5%) on that item only
    widget_discounted_price = apply_discount(100, bulk_discount_percent(10))
    widget_total = widget_discounted_price * 10
    # other items unchanged
    other_items_total = sub - 100*10
    subtotal_after_bulk = other_items_total + widget_total
    # coupon discount applies to whole subtotal after bulk? assumption: yes
    discounted_subtotal = apply_discount(subtotal_after_bulk, parse_coupon('SAVE5'))
    expected_total = discounted_subtotal
    if discounted_subtotal < 1000:
        expected_total += 30  # member half shipping
    assert round(total, 2) == round(expected_total, 2)

# ---------- Edge cases for Cart total ----------

def test_cart_total_coupon_and_shipping_edge():
    c = Cart()
    c.add_item('expensive', 500, 3)  # subtotal 1500
    # Should get free shipping due to subtotal >=1000 even after discounts
    t = c.total(coupon='SAVE50')
    assert t == apply_discount(1500, 50)

# End of tests
