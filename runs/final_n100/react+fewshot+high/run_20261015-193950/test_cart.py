import pytest
import cart

def _bulk_discount_percent(quantity: int) -> int:
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

@pytest.mark.parametrize("price,percent,expected", [
    (200.0, 15, 170.00),
    (100.0, 0, 100.00),
    (100.0, 100, 0.00),
    # rounding example
    (50.555, 10, 45.50),
])
def test_apply_discount(price, percent, expected):
    result = cart.apply_discount(price, percent)
    assert round(result, 2) == expected

@pytest.mark.parametrize("price,percent", [
    (-1.0, 10),          # negative price
    (100.0, -5),         # percent below 0
    (100.0, 101),        # percent above 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "ten"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Valid coupons
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save1", 1),
    (" SAVE50 ", 50),
    ("sAvE45", 45),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupons
@pytest.mark.parametrize("invalid_code", [
    "SAV10",
    "SAVE0",
    "SAVE51",
    "SAVE-5",
    "something else",
    "SAVE10X",
    "",
    "   ",
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# Shipping fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (800, True, 30),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10.5, -1, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

def test_shipping_fee_exact_threshold():
    assert cart.shipping_fee(1000, member=False) == 0
    assert cart.shipping_fee(1000, member=True) == 0

# Cart tests
def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert round(c.subtotal(), 2) == 0.00
    assert round(c.total(), 2) == 0.00


def test_items_returns_copy():
    c = cart.Cart()
    c.add_item('apple', 1.0)
    copy_dict = c.items()
    copy_dict['banana'] = 10
    assert 'banana' not in c.items()
    assert copy_dict is not c.items()


def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item('apple', 2.0, quantity=5)
    assert c.items() == {'apple': 5}
    assert round(c.subtotal(), 2) == 10.00

    c.add_item('apple', 2.0, quantity=6)
    expected_apple_total = round(2.0 * 11 * (1 - _bulk_discount_percent(11)/100), 2)
    assert round(c.subtotal(), 2) == expected_apple_total

    c.add_item('banana', 1.5, quantity=12)
    apple_discounted = round(2.0 * 11 * (1 - _bulk_discount_percent(11)/100), 2)
    banana_discounted = round(1.5 * 12 * (1 - _bulk_discount_percent(12)/100), 2)
    expected_total = round(apple_discounted + banana_discounted, 2)
    assert round(c.subtotal(), 2) == expected_total


def test_add_item_error_conditions():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('apple', -1.0, quantity=5)
    with pytest.raises(ValueError):
        c.add_item('banana', 2.0, quantity=0)
    with pytest.raises(ValueError):
        c.add_item('orange', 1.0, quantity=-3)
    with pytest.raises(ValueError):
        c.add_item('pear', 1.0, quantity=2.5)
    c.add_item('apple', 2.0, quantity=3)
    with pytest.raises(ValueError):
        c.add_item('apple', 3.0, quantity=1)


def test_remove_item_and_removal_logic():
    c = cart.Cart()
    c.add_item('apple', 2.0, quantity=5)
    c.add_item('banana', 1.5, quantity=12)

    c.remove_item('apple', quantity=2)
    assert c.items() == {'apple': 3, 'banana': 12}
    apple_discounted = round(2.0 * 3 * (1 - _bulk_discount_percent(3)/100), 2)
    banana_discounted = round(1.5 * 12 * (1 - _bulk_discount_percent(12)/100), 2)
    expected_subtotal = round(apple_discounted + banana_discounted, 2)
    assert round(c.subtotal(), 2) == expected_subtotal

    c.remove_item('apple', quantity=3)
    assert 'apple' not in c.items()
    banana_only = round(1.5 * 12 * (1 - _bulk_discount_percent(12)/100), 2)
    assert round(c.subtotal(), 2) == banana_only

    c.remove_item('banana', quantity=20)
    assert c.items() == {}
    assert round(c.subtotal(), 2) == 0.00

    with pytest.raises(KeyError):
        c.remove_item('pear')


def test_subtotal_bulk_discount_boundaries():
    c = cart.Cart()
    boundaries = [
        ('low', 9),
        ('ten', 10),
        ('fifty', 49),
        ('hundred', 50),
        ('ninety_nine', 99),
        ('hundred_plus', 100)
    ]
    for name, qty in boundaries:
        c.add_item(name, 1.0, quantity=qty)

    expected = 0.0
    for _, qty in boundaries:
        percent = _bulk_discount_percent(qty)
        amount = 1.0 * qty
        discounted = amount * (1 - percent/100)
        expected += discounted
    assert round(c.subtotal(), 2) == round(expected, 2)


def test_subtotal_rounding_per_item():
    c = cart.Cart()
    c.add_item('itemA', 0.11, quantity=10)
    c.add_item('itemB', 0.11, quantity=10)

    percent = _bulk_discount_percent(10)
    unrounded_discounted = 0.11 * 10 * (1 - percent/100)
    expected_total = round(unrounded_discounted + unrounded_discounted, 2)
    assert round(c.subtotal(), 2) == expected_total


def test_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item('small', 100.0, quantity=5)
    expected_subtotal = 500.0
    shipping = 60
    total_expected = round(expected_subtotal + shipping, 2)
    assert round(c.total(), 2) == total_expected


def test_total_no_coupon_member():
    c = cart.Cart()
    c.add_item('small', 100.0, quantity=5)
    expected_subtotal = 500.0
    shipping = 30
    total_expected = round(expected_subtotal + shipping, 2)
    assert round(c.total(member=True), 2) == total_expected


def test_total_no_coupon_free_shipping():
    c = cart.Cart()
    c.add_item('expensive', 1200.0, quantity=1)
    expected_subtotal = 1200.0
    shipping = 0
    total_expected = round(expected_subtotal + shipping, 2)
    assert round(c.total(), 2) == total_expected


def test_total_with_coupon_and_rounding():
    c = cart.Cart()
    c.add_item('item', 12.345, quantity=10)
    discounted_amount = round(123.45 * (1 - 0.07), 2)
    shipping = 60
    total_expected = round(discounted_amount + shipping, 2)
    assert round(c.total(coupon="SAVE7"), 2) == total_expected


def test_total_with_coupon_member():
    c = cart.Cart()
    c.add_item('item', 12.345, quantity=10)
    discounted_amount = round(123.45 * (1 - 0.07), 2)
    shipping = 30
    total_expected = round(discounted_amount + shipping, 2)
    assert round(c.total(member=True, coupon="SAVE7"), 2) == total_expected


def test_total_coupon_invalid():
    c = cart.Cart()
    c.add_item('small', 100.0, quantity=5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")


def test_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert round(c.total(), 2) == 0.00
    assert round(c.total(coupon="SAVE10"), 2) == 0.00


def test_total_free_shipping_after_coupon():
    c = cart.Cart()
    c.add_item('expensive', 200.0, quantity=6)
    discounted_amount = round(1200 * (1 - 0.10), 2)
    shipping = 0
    total_expected = round(discounted_amount + shipping, 2)
    assert round(c.total(coupon="SAVE10"), 2) == total_expected
