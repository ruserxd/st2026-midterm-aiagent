import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price/percent for apply_discount
@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("qty,exp", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount(qty, exp):
    assert cart.bulk_discount_percent(qty) == exp

# parse_coupon valid
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20 ", 20),
    ("   SaVe50", 50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# parse_coupon invalid
@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "BAD10",
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (1200, False, 0),
    (500, True, 30),
    (500, False, 60),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# Cart operations: add, remove, items
def test_cart_add_and_remove():
    c = cart.Cart()
    c.add_item("apple", 5.0, 2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 5.0, 3)
    assert c.items() == {"apple": 4}
    c.remove_item("apple", 1)
    assert c.items() == {"apple": 3}
    c.remove_item("apple", 3)
    assert c.items() == {}

# duplicate price mismatch raises ValueError
def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("orange", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.0, 1)

# remove non-existent item raises KeyError
def test_remove_missing():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# subtotal calculation with bulk discounts
def test_subtotal_with_bulk():
    c = cart.Cart()
    c.add_item("item", 10.0, 10)  # bulk discount 5%
    assert c.subtotal() == 95.0
    c.add_item("other", 20.0, 50)  # bulk discount 10% for other
    # subtotal: item 95 + other 1000 * 0.90 = 900 => 995
    assert c.subtotal() == 995.0

# total with coupon and shipping
def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("prod", 20.0, 3)
    # subtotal 60, no bulk discount
    # apply coupon SAVE10 -> 54
    # shipping fee for non-member: 60 => 114
    assert c.total(member=False, coupon="SAVE10") == 114.0
