import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ---------------------------------

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(20) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(60) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ---------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE5 ") == 5

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEX", "SAVe-1"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------

def test_shipping_fee_free_and_membership():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    # member discount
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item('apple', 2, quantity=3)
    c.add_item('banana', 1.5)
    assert c.items() == {'apple': 3, 'banana': 1}


def test_cart_add_existing_price_mismatch():
    c = cart.Cart()
    c.add_item('orange', 3)
    with pytest.raises(ValueError):
        c.add_item('orange', 4)


def test_cart_remove_item_and_negative_behavior():
    c = cart.Cart()
    c.add_item('pear', 5, quantity=2)
    c.remove_item('pear')
    assert c.items() == {'pear': 1}
    # removing more than exists should delete
    c.remove_item('pear', quantity=2)
    assert 'pear' not in c.items()

@ pytest.mark.parametrize("name", ["mango", "grape"])
def test_cart_remove_nonexistent(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name)

# Subtotal calculations including bulk discounts and rounding

def test_cart_subtotal_bulk_and_rounding():
    c = cart.Cart()
    c.add_item('pen', 10, quantity=12)   # bulk discount 5%
    assert c.subtotal() == round(10*12 * 0.95, 2)

# Total calculation with coupon and shipping (should use after-coupon amount for shipping but implementation uses subtotal)

def test_cart_total_without_coupon_and_nonmember():
    c = cart.Cart()
    c.add_item('book', 20, quantity=1)   # subtotal 20
    assert c.total() == round(20 + 60, 2)


def test_cart_total_with_member_discount_shipping():
    c = cart.Cart()
    c.add_item('tshirt', 30, quantity=1)
    assert c.total(member=True) == round(30 + 30, 2)  # half shipping


def test_cart_total_with_coupon_and_after_couponshipping_bug():
    # This test will expose the bug: shipping is based on subtotal instead of amount after coupon.
    c = cart.Cart()
    c.add_item('laptop', 1000, quantity=1)
    # With a large coupon that would make total < 1000, shipping should be free if using amount
    assert c.total(coupon="SAVE50") == pytest.approx(500)  # expecting no shipping because after discount less than threshold

# Empty cart total returns 0

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
