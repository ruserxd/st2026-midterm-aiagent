import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- helper for rounding ----------

def round2(x):
    return round(float(x), 2)

# ----- tests for apply_discount -----
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == round2(result)

# negative price or percent out of range should raise ValueError
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ----- tests for bulk_discount_percent -----
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
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----- tests for parse_coupon -----
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "", "SAVExx", "1234", "SAVE0", "SAVE51", "NOTACODE", "SAVE-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- tests for shipping_fee -----
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    shipping_fee(-10)

# ----- tests for Cart class -----
@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def filled_cart():
    cart = Cart()
    cart.add_item("apple", 1.00, quantity=3)   # subtotal 3.0
    cart.add_item("banana", 0.50, quantity=10) # subtotal 5.0 -> discount 5%? bulk
    return cart

# items list should reflect added items

def test_cart_items(empty_cart):
    assert empty_cart.items() == []
    empty_cart.add_item("test", 2.5)
    assert empty_cart.items() == [("test", 2.5, 1)]

def test_remove_item(filled_cart):
    # remove part of quantity
    filled_cart.remove_item("banana", quantity=3)
    assert any(name=="banana" and qty==7 for name,price,qty in filled_cart.items())
    # removing more than existing should raise ValueError
    with pytest.raises(ValueError):
        filled_cart.remove_item("banana", quantity=10)

# subtotal calculation

def test_subtotal(filled_cart):
    assert round2(filled_cart.subtotal()) == 8.0  # 3*1 + 10*0.5 = 8.0

# total without coupon/member

def test_total_no_discount(empty_cart):
    empty_cart.add_item("item", 30)
    # subtotal 30, shipping fee 60 -> total 90 rounded
    assert empty_cart.total() == round2(30 + 60)

# with member discount: no discount but half shipping

def test_total_member(empty_cart):
    empty_cart.add_item("item", 30)
    assert empty_cart.total(member=True) == round2(30 + 30)  # half of 60

# with coupon

def test_total_coupon(filled_cart):
    # subtotal 8.0, coupon SAVE10 -> discount 10% => 7.20
    total = filled_cart.total(coupon="SAVE10")
    # shipping fee based on subtotal after coupon (should be 60 because <1000)
    expected = round2(7.20 + 60)
    assert total == expected

# test the bug: shipping_fee should use discounted amount but implementation uses original subtotal

def test_total_shipping_bug(filled_cart):
    # if we compute expected using spec: shipping based on amount after coupon
    discounted_amount = round2(8.0 * 0.90)  # 10% off
    expected = round2(discounted_amount + shipping_fee(discounted_amount, False))
    actual = filled_cart.total(coupon="SAVE10")
    assert actual != expected, "Implementation does not use discounted subtotal for shipping"
