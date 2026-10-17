import pytest
import cart

# Test apply_discount – normal cases and invalid inputs.

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0
    # rounding to two decimals
    assert cart.apply_discount(99.999, 10) == round(99.999 * (1 - 10 / 100), 2)

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent – boundaries and invalid inputs.
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, '10'])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Test parse_coupon – valid (case‑insensitive) and invalid codes.
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SaVe30 ", 30),
    ("SAVE50", 50),   # boundary
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", [
    "SAVEX",
    "SAVE0",
    "INVALID",
    "",
    None,
    "   ",
    "SAVE101",
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# Test shipping_fee – threshold behaviour, member discount and negative values.
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for the Cart class.
# Adding items – new, increasing quantity, price mismatch and validation.

def test_cart_add_item_new():
    c = cart.Cart()
    c.add_item('apple', 1.0)
    assert c.items() == {'apple': 1}

def test_cart_add_item_increase_quantity_same_price():
    c = cart.Cart()
    c.add_item('banana', 2.5, quantity=3)
    c.add_item('banana', 2.5, quantity=2)
    assert c.items() == {'banana': 5}

def test_cart_add_item_different_price_error():
    c = cart.Cart()
    c.add_item('orange', 1.0)
    with pytest.raises(ValueError):
        c.add_item('orange', 2.0)

@pytest.mark.parametrize("unit_price", [-1.0, -5])
def test_cart_add_item_invalid_unit_price(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('test', unit_price, quantity=1)

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_cart_add_item_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('test', 10.0, quantity=quantity)

# Removing items – errors and quantity adjustments.

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

def test_cart_remove_more_than_quantity_deletes():
    c = cart.Cart()
    c.add_item('pear', 1.5, quantity=2)
    c.remove_item('pear', quantity=3)  # removes more than present
    assert 'pear' not in c.items()

def test_cart_remove_less_quantity_reduces():
    c = cart.Cart()
    c.add_item('plum', 2.0, quantity=5)
    c.remove_item('plum', quantity=3)
    assert c.items() == {'plum': 2}

def test_cart_remove_equal_quantity_deletes_per_spec():
    c = cart.Cart()
    c.add_item('peach', 1.0, quantity=2)
    c.remove_item('peach', quantity=2)
    assert 'peach' not in c.items()

# Subtotal calculations.

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_subtotal_no_bulk_discount():
    c = cart.Cart()
    c.add_item('widget', 20.0, quantity=3)
    expected = round(20.0 * 3 * (1 - 0 / 100), 2)
    assert c.subtotal() == expected

def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item('gadget', 5.0, quantity=12)  # bulk discount 5%
    expected = round(5.0 * 12 * (1 - 5 / 100), 2)
    assert c.subtotal() == expected

def test_cart_subtotal_multiple_items_with_discounts():
    c = cart.Cart()
    c.add_item('y', 10.0, quantity=50)   # 10% discount
    c.add_item('z', 20.0, quantity=5)    # no bulk discount
    line1 = round(10.0 * 50 * (1 - 10 / 100), 2)
    line2 = round(20.0 * 5 * (1 - 0 / 100), 2)
    expected_total = round(line1 + line2, 2)
    assert c.subtotal() == expected_total

# Total calculations – various scenarios.

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item('item', 10.0, quantity=5)
    subtotal = round(10.0 * 5 * (1 - 0 / 100), 2)   # 50
    shipping = cart.shipping_fee(subtotal, member=False)
    assert c.total() == round(subtotal + shipping, 2)

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item('item', 10.0, quantity=5)
    subtotal = round(10.0 * 5 * (1 - 0 / 100), 2)   # 50
    shipping = cart.shipping_fee(subtotal, member=True)
    assert c.total(member=True) == round(subtotal + shipping, 2)

def test_cart_total_coupon_no_threshold_cross():
    c = cart.Cart()
    c.add_item('item', 20.0, quantity=5)   # subtotal 100
    amount_after_discount = cart.apply_discount(100, 10)  # 90
    shipping_expected = cart.shipping_fee(amount_after_discount, member=False)
    assert c.total(coupon="SAVE10") == round(amount_after_discount + shipping_expected, 2)

def test_cart_total_coupon_cross_threshold_non_member():
    c = cart.Cart()
    c.add_item('exp1', 700.0, quantity=1)
    c.add_item('exp2', 400.0, quantity=1)   # subtotal 1100
    amount_after_discount = cart.apply_discount(1100, 10)  # 990
    shipping_expected = cart.shipping_fee(amount_after_discount, member=False)
    expected_total = round(amount_after_discount + shipping_expected, 2)
    assert c.total(coupon="SAVE10") == expected_total

def test_cart_total_coupon_cross_threshold_member():
    c = cart.Cart()
    c.add_item('exp1', 700.0, quantity=1)
    c.add_item('exp2', 400.0, quantity=1)   # subtotal 1100
    amount_after_discount = cart.apply_discount(1100, 10)  # 990
    shipping_expected = cart.shipping_fee(amount_after_discount, member=True)
    expected_total = round(amount_after_discount + shipping_expected, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('item', 10.0)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
