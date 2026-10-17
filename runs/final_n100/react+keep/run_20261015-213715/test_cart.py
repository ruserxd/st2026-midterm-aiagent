import pytest
import cart
from math import isclose

def approx(value, target, tol=1e-2):
    return isclose(value, target, abs_tol=tol)

# ---------- Tests for utility functions ----------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk discount

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse coupon

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("   SaVe30   ") == 30

@pytest.mark.parametrize("code", ["SAV5", "abc10", "", "SAVE-10", "SAVE101"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee

def test_shipping_fee():
    assert cart.shipping_fee(0, False) == 60
    assert cart.shipping_fee(500, True) == 30
    assert cart.shipping_fee(999.99, False) == 60
    assert cart.shipping_fee(1000, False) == 0
    assert cart.shipping_fee(1500, True) == 0

@pytest.mark.parametrize("subtotal", [-10])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items()["apple"] == 5
    # unit price mismatch raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5)

@pytest.mark.parametrize("price,qty", [( -1, 1), (1,0)])
def test_cart_add_invalid(price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", price, qty)

# subtotal calculations

def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("item", 20.0, 4)  # quantity <10 -> no bulk discount
    assert approx(c.subtotal(), 80.0)

# coupon handling in total

def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    amount_without = c.subtotal()
    # apply coupon discount
    after_discount = cart.apply_discount(amount_without, cart.parse_coupon("SAVE20"))
    shipping = cart.shipping_fee(after_discount, False)
    assert approx(c.total(coupon="SAVE20"), after_discount + shipping)

# test that empty cart cost 0 without shipping

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

# test remove item

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("item", 10, 5)
    c.remove_item("item", 3)
    assert c.items()["item"] == 2
    # removing more than present should delete item
    c.remove_item("item", 5)
    assert "item" not in c.items()

# test remove non-existing raises KeyError

def test_cart_remove_missing():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("ghost")

# test total for member vs non-member shipping calculation

def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    subtotal = c.subtotal()
    # Non-member: full shipping
    assert approx(c.total(member=False), subtotal + cart.shipping_fee(subtotal, False))
    # Member: half shipping
    assert approx(c.total(member=True), subtotal + cart.shipping_fee(subtotal, True))

# test that coupon applies before shipping but implementation incorrectly uses subtotal for shipping

def test_cart_total_shipping_bug_detected():
    c = cart.Cart()
    c.add_item("item", 200, 1)
    # With a 10% coupon, total before shipping should be 180.
    # Shipping fee for subtotal 200 is 60, so expected final = 240
    assert approx(c.total(coupon="SAVE10"), 240.0)
