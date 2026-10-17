import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (0.0, 0, 0.0),
        (100.0, 0, 100.0),
        (100.0, 100, 0.0),
        (200.0, 15, 170.0),
        (199.99, 10, round(199.99 * 0.9, 2)),
        (123.456, 33, round(123.456 * 0.67, 2)),
    ]
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize(
    "price, percent",
    [
        (-1.0, 10),
        (10.0, -5),
        (10.0, 101),
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0), (10, 5), (49, 5),
        (50, 10), (99, 10),
        (100, 15), (101, 15)
    ]
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 2.5]
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("  SaVe5  ", 5),
        ("SAVE50", 50)
    ]
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVExx", "SAVEE", "save0", "save51", "abc10", "SAVE", ""]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000.0, False, 0),
        (999.99, False, 60),
        (999.99, True, 30),
        (0.0, False, 60),
        (1200.0, True, 0)
    ]
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1.0, -100]
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
def test_cart_init_empty():
    c = cart.Cart()
    assert c.items() == {}

def test_cart_add_new_item():
    c = cart.Cart()
    c.add_item('apple', 1.5, quantity=3)
    assert c.items() == {'apple': 3}
    expected_subtotal = round(1.5 * 3 * (1 - cart.bulk_discount_percent(3) / 100), 2)
    assert c.subtotal() == pytest.approx(expected_subtotal)

def test_cart_add_existing_increases_quantity():
    c = cart.Cart()
    c.add_item('banana', 2.0, quantity=1)
    c.add_item('banana', 2.0, quantity=2)
    assert c.items() == {'banana': 3}

def test_cart_add_existing_price_mismatch():
    c = cart.Cart()
    c.add_item('orange', 1.0, quantity=2)
    with pytest.raises(ValueError):
        c.add_item('orange', 1.5, quantity=1)

@pytest.mark.parametrize(
    "unit_price, quantity",
    [(-1.0, 1), (1.0, 0), (1.0, -3), (1.0, 2.5)]
)
def test_cart_add_item_invalid(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('test', unit_price=unit_price, quantity=quantity)

def test_cart_remove_partial_and_full():
    c = cart.Cart()
    c.add_item('apple', 1.0, quantity=5)
    c.remove_item('apple', quantity=2)
    assert c.items() == {'apple': 3}
    c.remove_item('apple', quantity=4)  # removes more than remaining
    assert 'apple' not in c.items()

def test_cart_remove_exact_quantity():
    c = cart.Cart()
    c.add_item('apple', 1.0, quantity=3)
    c.remove_item('apple', quantity=3)
    assert 'apple' not in c.items()

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 2.5]
)
def test_cart_remove_invalid_quantity(quantity):
    c = cart.Cart()
    c.add_item('apple', 1.0, quantity=3)
    with pytest.raises(ValueError):
        c.remove_item('apple', quantity=quantity)

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('banana', quantity=1)

def test_cart_items_copy_independent():
    c = cart.Cart()
    c.add_item('apple', 1.0, quantity=2)
    d = c.items()
    d['apple'] = 999
    assert c.items() == {'apple': 2}

def test_cart_subtotal_complex():
    c = cart.Cart()
    c.add_item('apple', 10.0, quantity=5)   # no discount
    c.add_item('banana', 20.0, quantity=15) # 5% discount
    c.add_item('egg', 3.333, quantity=12)   # 5% discount with rounding
    expected = 50 + 285 + round(3.333 * 12 * (1 - cart.bulk_discount_percent(12)/100), 2)
    assert c.subtotal() == pytest.approx(expected)

def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item('apple', 10.0, quantity=5)   # subtotal 50
    c.add_item('banana', 20.0, quantity=15) # subtotal after discount 285
    expected_subtotal = 335
    assert c.subtotal() == pytest.approx(expected_subtotal)
    expected_total = expected_subtotal + 60  # non-member shipping
    assert c.total(member=False) == pytest.approx(expected_total)

def test_cart_total_member():
    c = cart.Cart()
    c.add_item('apple', 10.0, quantity=5)
    c.add_item('banana', 20.0, quantity=15)
    expected_subtotal = 335
    assert c.total(member=True) == pytest.approx(expected_subtotal + 30)

def test_cart_total_coupon():
    c = cart.Cart()
    c.add_item('apple', 10.0, quantity=5)
    c.add_item('banana', 20.0, quantity=15)
    expected_total = 335 * (1 - 0.10) + 60
    assert c.total(coupon='SAVE10') == pytest.approx(expected_total)

def test_cart_total_coupon_member():
    c = cart.Cart()
    c.add_item('apple', 10.0, quantity=5)
    c.add_item('banana', 20.0, quantity=15)
    expected_total = 335 * (1 - 0.10) + 30
    assert c.total(member=True, coupon='SAVE10') == pytest.approx(expected_total)

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item('apple', 10.0, quantity=5)
    with pytest.raises(ValueError):
        c.total(coupon='BADCODE')

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_shipping_fee_free_after_coupon_below_threshold():
    c = cart.Cart()
    c.add_item('expensive', 200.0, quantity=10)
    # subtotal before coupon is 1900
    expected_subtotal_before_coupon = round(200.0 * 10 * (1 - cart.bulk_discount_percent(10)/100), 2)
    assert expected_subtotal_before_coupon == pytest.approx(1900.0)
    assert c.total() == pytest.approx(expected_subtotal_before_coupon)

def test_cart_shipping_fee_applied_after_coupon_below_threshold():
    c = cart.Cart()
    c.add_item('expensive', 200.0, quantity=10)
    new_subtotal = 1900 * (1 - 0.50)  # 950
    expected_total = new_subtotal + 60
    assert c.total(coupon='SAVE50') == pytest.approx(expected_total)

def test_cart_shipping_fee_applied_after_coupon_below_threshold_member():
    c = cart.Cart()
    c.add_item('expensive', 200.0, quantity=10)
    new_subtotal = 1900 * (1 - 0.50)  # 950
    expected_total = new_subtotal + 30
    assert c.total(member=True, coupon='SAVE50') == pytest.approx(expected_total)

def test_cart_shipping_fee_free_after_coupon_above_threshold():
    c = cart.Cart()
    c.add_item('expensive', 200.0, quantity=10)
    new_subtotal = 1900 * (1 - 0.25)  # 1425
    assert c.total(coupon='SAVE25') == pytest.approx(new_subtotal)

def test_cart_shipping_fee_free_after_coupon_above_threshold_member():
    c = cart.Cart()
    c.add_item('expensive', 200.0, quantity=10)
    new_subtotal = 1900 * (1 - 0.25)  # 1425
    assert c.total(member=True, coupon='SAVE25') == pytest.approx(new_subtotal)
