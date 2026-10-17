import pytest
import cart

# ---- apply_discount ----
@ pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@ pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent ----
@ pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@ pytest.mark.parametrize("qty", [0, -5, 3.7])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon ----
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVEXX",
    "", "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee ----
@ pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (50, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# Adding items
c = cart.Cart()
c.add_item("apple", 1.00, 2)
assert c.items() == {"apple": 2}
assert c.subtotal() == 2.00
# bulk discount should apply when quantity >=10
c.add_item("apple", 1.00, 8)  # total quantity now 10
assert c.subtotal() == 9.5

# Adding different item
c.add_item("banana", 0.50, 20)
expected_banana = 20*0.5*(1- cart.bulk_discount_percent(20)/100)
assert c.subtotal() == 9.5 + expected_banana

# Removing items partially
c.remove_item("apple", 5)
assert c.items()["apple"] == 5
expected_apple = 5*1.00*(1- cart.bulk_discount_percent(5)/100)
assert c.subtotal() == expected_apple + expected_banana

# Remove remaining apples, item should be removed
c.remove_item("apple", 5)
assert "apple" not in c.items()
assert c.subtotal() == expected_banana

# removing non-existent item raises KeyError
with pytest.raises(KeyError):
    c.remove_item("orange", 1)

# total with coupon and shipping
c = cart.Cart()
c.add_item("widget", 100, 5)  # no bulk discount
subtotal_before = 500
assert c.subtotal() == subtotal_before
# apply coupon SAVE10 -> 10%
total_after_coupon = subtotal_before * 0.9 + cart.shipping_fee(subtotal_before*0.9)
assert c.total(coupon="SAVE10") == round(total_after_coupon,2)

# total with member shipping discount
c = cart.Cart()
c.add_item("gadget", 50, 4)  # 200 subtotal
assert c.total(member=True) == round(200 + 30,2)
