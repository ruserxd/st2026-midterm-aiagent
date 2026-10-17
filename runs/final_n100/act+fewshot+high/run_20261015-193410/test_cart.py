import pytest
import cart

# apply_discount tests
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_edges(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

def test_apply_discount_rounding():
    price = 99
    percent = 33
    expected = round(price * (1 - percent / 100), 2)
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-10, 20),
    (50, -5),
    (50, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),   # spec-valid but implementation fails
    ("   SaVe30   ", 30) # mixed case; implementation fails
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEE10", "SAVETWELVE", " save0 "])
def test_parse_coupon_invalid_format(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_parse_coupon_non_string():
    with pytest.raises(ValueError):
        cart.parse_coupon(None)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (1200, True, 0),
    (999.99, False, 60),
    (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
def test_cart_add_new_item():
    c = cart.Cart()
    c.add_item('apple', 2.0, 3)
    assert c.items() == {'apple': 3}
    assert c.subtotal() == round(2.0 * 3, 2)

def test_cart_add_existing_same_price():
    c = cart.Cart()
    c.add_item('apple', 2.0, 3)
    c.add_item('apple', 2.0, 5)
    assert c.items() == {'apple': 8}

def test_cart_add_existing_different_price():
    c = cart.Cart()
    c.add_item('apple', 2.0, 3)
    with pytest.raises(ValueError):
        c.add_item('apple', 1.5, 2)

def test_cart_add_invalid_parameters():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('apple', -1.0, 3)
    with pytest.raises(ValueError):
        c.add_item('apple', 2.0, 0)

def test_cart_remove_existing():
    c = cart.Cart()
    c.add_item('apple', 2.0, 5)
    c.remove_item('apple', 3)
    assert c.items() == {'apple': 2}

def test_cart_remove_to_zero_removes_item():
    c = cart.Cart()
    c.add_item('banana', 1.0, 2)
    c.remove_item('banana', 2)  # should remove the item completely
    assert 'banana' not in c.items()

def test_cart_remove_beyond_quantity_deletes():
    c = cart.Cart()
    c.add_item('orange', 3.0, 1)
    c.remove_item('orange', 5)
    assert 'orange' not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('pear')

def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item('item1', 10.0, 12)   # bulk discount 5%
    c.add_item('item2', 5.0, 3)     # no bulk discount
    expected_line1 = round(10.0 * 12 * (1 - cart.bulk_discount_percent(12)/100), 2)
    expected_line2 = round(5.0 * 3 * (1 - cart.bulk_discount_percent(3)/100), 2)
    assert c.subtotal() == round(expected_line1 + expected_line2, 2)

def test_cart_empty_subtotal():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon_member_false():
    c = cart.Cart()
    c.add_item('item', 1200, 1)
    assert c.total(member=False) == 1200

def test_cart_total_with_coupon_cross_threshold():
    c = cart.Cart()
    c.add_item('item', 1200, 1)
    total = c.total(coupon='SAVE25')
    # Spec expects discounted amount + shipping on discounted subtotal
    discounted = round(1200 * (1 - 25 / 100), 2)   # 900.0
    expected_shipping = cart.shipping_fee(discounted, False)  # 60
    expected_spec_total = round(discounted + expected_shipping, 2)
    assert total == expected_spec_total

def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item('item', 500, 1)
    assert c.total(member=True) == 530  # 500 + 30

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item('item', 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon='INVALID')
