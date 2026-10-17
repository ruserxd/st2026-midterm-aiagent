import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),            # example
    (100, 0, 100.0),             # no discount
    (50, 100, 0.0),              # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# apply_discount error cases
@pytest.mark.parametrize("price,percent", [
    (-10, 10),   # negative price
    (10, -5),    # negative percent
    (10, 105),   # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# bulk_discount_percent error
@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE25 ", 25),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

# parse_coupon errors
@pytest.mark.parametrize("code", ["SAVE0", "SAVEX", "10SAVE", "save51", "" , " "])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# shipping_fee error
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # add same item increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # adding different price raises
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5, 1)
    # invalid quantity or unit_price
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, 0)

def test_cart_remove_and_subtotal():
    c = cart.Cart()
    c.add_item("item", 10.0, 20)  # 20 units -> bulk discount 15%
    # subtotal should be 10*20=200 minus 15% = 170.00
    assert c.subtotal() == 170.00
    # remove some
    c.remove_item("item", 5)
    # now 15 units -> bulk discount 10%: 10*15=150 minus 10%=135
    assert c.subtotal() == 135.00
    # remove all remaining
    c.remove_item("item", 15)
    assert c.items() == {}
    assert c.subtotal() == 0
    # removing non-existent item raises
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_cart_total_no_coupon_and_non_member():
    c = cart.Cart()
    c.add_item("small", 10.0, 2)  # no bulk discount -> subtotal 20
    total = c.total(member=False)
    # subtotal 20 + shipping 60 = 80
    assert total == 80.00

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("large", 500.0, 3)  # no bulk discount -> 1500
    total_before_shipping = 1500
    # apply coupon SAVE10 -> 1350
    total_after_coupon = cart.apply_discount(total_before_shipping, 10)
    # shipping fee for member on 1350 is free (>=1000)
    expected_total = total_after_coupon  # no shipping
    assert c.total(member=True, coupon="SAVE10") == round(expected_total,2)

# test that an empty cart costs 0
def test_cart_empty_total():
    c = cart.Cart()
    assert c.total() == 0.00
