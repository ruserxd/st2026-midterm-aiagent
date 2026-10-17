import pytest
import cart

# helper for approximate equality due to rounding
EPS = 1e-9

# ---- apply_discount ----
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -5])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ----
@pytest.mark.parametrize("quantity, expected", [
    (9, 0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 1.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon ----
valid_cases = {
    "SAVE10":10,
    "save25":25,
    "  Save50  ":50,
    "save1":1,
}
for code, exp in valid_cases.items():
    assert cart.parse_coupon(code) == exp

invalid_codes = ["", "SAVEX", "SAVE0", "SAVE51", "X10", "  "]
for code in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee ----
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (1200, True, 0),
    (999.99, False, 60),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----
def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 10.0, 3)
    assert c.items() == {"apple":3}
    # adding same item increases quantity
    c.add_item("apple", 10.0, 2)
    assert c.items() == {"apple":5}

    with pytest.raises(ValueError):
        # price mismatch
        c.add_item("apple", 9.0,1)

    c.remove_item("apple", 4)
    assert c.items() == {"apple":1}
    c.remove_item("apple", 1)  # should remove completely
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item("banana",1)

    # invalid quantity
    with pytest.raises(ValueError):
        c.add_item("pear",5.0,-2)

    with pytest.raises(ValueError):
        c.add_item("pear",-3,2)

# subtotal calculation with bulk discount
c = cart.Cart()
c.add_item("widget", 20.0, 12)  # quantity 12 -> 5% discount
assert c.subtotal() == round(20.0*12*(1-0.05),2)

# total with coupon and shipping
c.add_item("gadget", 100.0, 1)   # no bulk discount on gadget
subtotal = c.subtotal()
coupon_percent = cart.parse_coupon("SAVE10")
after_coupon = round(subtotal*(1-0.10),2)
expected_total = round(after_coupon + cart.shipping_fee(after_coupon, False),2)
assert c.total(coupon="SAVE10") == expected_total

# member discount affects shipping only
c2 = cart.Cart()
c2.add_item("thing", 500.0,1)
# subtotal 500, coupon none -> 500 shipping 60 for non-member, 30 for member
assert c2.total(member=True) == round(500+30,2)
assert c2.total(member=False) == round(500+60,2)
