import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price, percent", [
    (100, 0),          # no discount
    (100, 100),        # full discount
])
def test_apply_discount_edge(price, percent):
    expected = round(price * (1 - percent / 100.0) , 2)
    assert apply_discount(price, percent) == expected

# invalid cases
@ pytest.mark.parametrize("price, percent", [(-10, 20), (50, -5), (60, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_exact_thresholds():
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty, expected", [ (9,0), (49,0), (99,0) ])
def test_bulk_discount_no_discount(qty, expected):
    assert bulk_discount_percent(qty) == expected

@ pytest.mark.parametrize("qty", [0,-1,3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SavE50") == 50

@ pytest.mark.parametrize("code", ["save0", "SAVEXY", "abc", "SAVE51", " SAVE-5 "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(999.99, member=True) == 30
    # also check free for higher amounts
    assert shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class basic behaviour ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0

# adding items and bulk discount application

def test_cart_add_and_subtotal_bulk_discount():
    cart = Cart()
    # add 10 units, should get 5% discount on each unit
    cart.add_item("apple", 100.0, 10)
    expected_unit = apply_discount(100.0, bulk_discount_percent(10))
    assert cart.subtotal() == round(expected_unit * 10, 2)
    # add more of same item to cross threshold
    cart.add_item("apple", 100.0, 90)  # now total 100 units -> 15% discount
    expected_discount = bulk_discount_percent(100)
    discounted_price = apply_discount(100.0, expected_discount)
    assert cart.subtotal() == round(discounted_price * 100, 2)

# removing items and ensuring removal when zero

def test_cart_remove_and_removal():
    cart = Cart()
    cart.add_item("banana", 50.0, 5)
    cart.remove_item("banana", 3)
    assert cart.items() == {"banana": 2}
    # remove remaining to trigger deletion
    cart.remove_item("banana", 2)
    assert "banana" not in cart.items()
    with pytest.raises(KeyError):
        cart.remove_item("banana", 1)

# adding item with different price raises ValueError

def test_cart_add_price_mismatch():
    cart = Cart()
    cart.add_item("orange", 30.0, 2)
    with pytest.raises(ValueError):
        cart.add_item("orange", 35.0, 1)

# invalid quantity or price on add
@ pytest.mark.parametrize("unit_price, qty", [(-5, 1), (10, 0), (20, -3)])
def test_cart_add_invalid(unit_price, qty):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("pear", unit_price, qty)

# total calculation including coupon and shipping

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    # 2 items: 3 units of item A (no bulk discount), 5 units of B (bulk 10% on each because quantity=5? actually threshold is >=10 -> no discount)
    cart.add_item("A", 100.0, 3)   # subtotal 300
    cart.add_item("B", 50.0, 5)    # subtotal 250
    # total before coupon and shipping = 550
    assert cart.subtotal() == 550.0
    # apply a valid coupon 10%
    total_after_coupon = apply_discount(550.0, parse_coupon("SAVE10"))
    # shipping on this amount (member=False): subtotal>=1000? no -> fee 60
    expected_total = round(total_after_coupon + 60, 2)
    assert cart.total(coupon="SAVE10") == expected_total

# total with member discount in shipping

def test_cart_total_member_shipping_fee():
    cart = Cart()
    cart.add_item("C", 500.0, 3)   # subtotal 1500 -> free shipping
    assert cart.total(member=True) == 1500.0
    # add more to keep below threshold
    cart.remove_item("C", 1)
    cart.add_item("D", 100.0, 5)   # now subtotal 1200? actually 2*500 + 5*100 = 1000+500=1500 still; need adjust
    # let's use small amounts instead
    cart = Cart()
    cart.add_item("E", 200.0, 4)   # subtotal 800 -> shipping fee 60 normally, 30 if member
    assert cart.total(member=True) == round(800 + 30, 2)

# empty cart no shipping

def test_empty_cart_no_shipping():
    cart = Cart()
    assert cart.total() == 0.0
