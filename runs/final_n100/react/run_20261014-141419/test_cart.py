import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- helpers for floating comparison

def approx(value, *, rel=1e-9):
    return pytest.approx(value, rel=rel)

# ----------- tests for apply_discount -----------------

test_cases_apply = [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
]
@pytest.mark.parametrize("price,percent,expected", test_cases_apply)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

# invalid inputs
with pytest.raises(ValueError):
    apply_discount(-1, 10)
with pytest.raises(ValueError):
    apply_discount(100, -5)
with pytest.raises(ValueError):
    apply_discount(100, 120)

# --------- tests for bulk_discount_percent ----------
test_cases_bulk = [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
]
@pytest.mark.parametrize("qty,expected", test_cases_bulk)
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

with pytest.raises(ValueError):
    bulk_discount_percent(0)
with pytest.raises(ValueError):
    bulk_discount_percent(-5)

# --------- tests for parse_coupon --------------
test_cases_coupon = [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe30   ", 30),
]
@pytest.mark.parametrize("code,expected", test_cases_coupon)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_coupons = ["", "SAVE0", "SAVE51", "BAD10", "SAVEX"]
for code in invalid_coupons:
    with pytest.raises(ValueError):
        parse_coupon(code)

# --------- tests for shipping_fee -----------------
test_cases_shipping = [
    (0, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
]
@pytest.mark.parametrize("subtotal,expected", test_cases_shipping)
def test_shipping_fee(subtotal, expected):
    assert shipping_fee(subtotal) == expected

assert shipping_fee(200, member=True) == 30
with pytest.raises(ValueError):
    shipping_fee(-1)

# --------- Cart tests -------------------
cart = Cart()
# initial state
assert cart.items() == {}
assert cart.subtotal() == 0
assert cart.total() == 0

# adding items
cart.add_item("apple", 2.0, quantity=5)  # bulk discount 5% -> 10%? qty5 => no bulk (qty<10)
assert cart.items()["apple"] == 5
assert round(cart.subtotal(), 2) == 10.0  # 2*5 =10
# add more of same item
cart.add_item("apple", 2.0, quantity=6)  # total qty11 -> bulk discount 5%
assert cart.items()["apple"] == 11
expected_total = apply_discount(2.0 * 11, bulk_discount_percent(11))
assert round(cart.subtotal(), 2) == expected_total
# adding another item with different price
cart.add_item("banana", 1.5, quantity=3)
assert cart.items()["banana"] == 3

# test removing items
cart.remove_item("apple", quantity=4)
assert cart.items()["apple"] == 7
with pytest.raises(KeyError):
    cart.remove_item("orange")
# remove all banana
cart.remove_item("banana", quantity=3)
assert "banana" not in cart.items()

# test total with member and coupon
amount = cart.subtotal()
member_total = round(amount + shipping_fee(amount, member=True), 2)
assert cart.total(member=True) == member_total
# apply a coupon 10%
coupon_amount = apply_discount(amount, parse_coupon("SAVE10"))
expected = round(coupon_amount + shipping_fee(cart.subtotal(), member=False), 2)
assert cart.total(coupon="SAVE10") == expected

# empty cart total
empty_cart = Cart()
assert empty_cart.total() == 0

# verify rounding behaviour (edge cases)
cart.clear = lambda: None  # no clear, we will reinitialize
cart = Cart()
# quantity that triggers bulk discount
cart.add_item("item", 10.0, quantity=50)  # bulk discount 10%
assert cart.subtotal() == round(10.0 * 50 * (1 - 0.10), 2)

print('All tests passed.')
