import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Boundary and error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105, 150])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,result", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVExx", " "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),   # subtotal >= 1000 free shipping
    (999.99, True, 30),# member half fee when < 1000
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2.0, 3)
    c.add_item('banana', 1.5, 2)
    assert c.items() == {'apple': 3, 'banana': 2}

# Adding same item increases quantity and requires same price

def test_cart_add_same_item_price_check():
    c = cart.Cart()
    c.add_item('apple', 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item('apple', 3.0, 1)
    # correct price increases quantity
    c.add_item('apple', 2.0, 2)
    assert c.items() == {'apple': 3}

# Removing items

def test_cart_remove_items():
    c = cart.Cart()
    c.add_item('apple', 2.0, 5)
    c.remove_item('apple', 2)
    assert c.items() == {'apple': 3}
    # remove more than remaining removes item
    c.remove_item('apple', 4)
    assert c.items() == {}

# Removing non-existent item raises KeyError

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('orange', 1)

# Subtotal calculations including bulk discounts

def test_cart_subtotal():
    c = cart.Cart()
    # item A: quantity 12, unit price 10 - bulk discount 5%
    c.add_item('A', 10.0, 12)  # subtotal 120, discount 6 => 114
    # item B: quantity 55, unit price 20 - bulk discount 10%
    c.add_item('B', 20.0, 55)  # subtotal 1100, discount 110 => 990
    expected = round(114 + 990, 2)
    assert c.subtotal() == expected

# Total with coupon and shipping

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('item', 100.0, 10)  # bulk discount 5% -> 950
    total_with_coupon = 760.0   # 20% off
    expected_total = round(total_with_coupon + 60, 2)
    assert c.total(member=False, coupon='SAVE20') == expected_total

# Total with member free shipping when subtotal >= 1000

def test_cart_total_member_free_shipping():
    c = cart.Cart()
    c.add_item('expensive', 60.0, 20)
    # bulk discount 15% -> 1020
    assert c.subtotal() == round(60*20*(1-0.15),2)
    expected_total = round(c.subtotal(), 2)   # free shipping
    assert c.total(member=True) == expected_total

# Empty cart totals zero and no shipping

def test_cart_empty():
    c = cart.Cart()
    assert c.subtotal() == 0.0
    assert c.total() == 0.0
