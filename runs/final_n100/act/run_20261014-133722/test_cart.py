import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent -----------------------------------------

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(1500) == 15

@ pytest.mark.parametrize("q", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(q):
    with pytest.raises(ValueError):
        bulk_discount_percent(q)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE5 ") == 5

@ pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "10SAVE", ""])
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(5000, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart functionality ---------------------------------------------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_item():
    c = Cart()
    c.add_item("apple", 100, quantity=2)
    assert c.items() == {"apple": 2}
    # same item with same price increases quantity
    c.add_item("apple", 100, quantity=3)
    assert c.items() == {"apple": 5}
    # adding different item
    c.add_item("banana", 50)
    assert c.items() == {"apple": 5, "banana": 1}

    with pytest.raises(ValueError):
        c.add_item("apple", 90)  # price mismatch
    with pytest.raises(ValueError):
        c.add_item("pear", -10)
    with pytest.raises(ValueError):
        c.add_item("pear", 10, quantity=0)

    # remove some quantity
    c.remove_item("apple", quantity=2)
    assert c.items() == {"apple": 3, "banana": 1}
    # removing more than present removes item entirely
    c.remove_item("apple", quantity=5)
    assert c.items() == {"banana": 1}
    with pytest.raises(KeyError):
        c.remove_item("orange")

# ---------- subtotal with bulk discount ----------------------------------

def test_subtotal_with_bulk_discount():
    c = Cart()
    # 10 apples, bulk discount 5%
    c.add_item("apple", 100, quantity=10)
    assert bulk_discount_percent(10) == 5
    expected = apply_discount(100*10, 5)
    assert c.subtotal() == round(expected, 2)
    # 51 bananas, discount 10%
    c.add_item("banana", 20, quantity=51)
    subtotal_expected = round(
        apply_discount(100*10, 5) + apply_discount(20*51, 10), 2
    )
    assert c.subtotal() == subtotal_expected

# ---------- total calculation --------------------------------------------

def test_total_no_coupon():
    c = Cart()
    c.add_item("apple", 200, quantity=1)
    # subtotal 200, shipping 60 => 260
    assert c.total() == round(200 + 60, 2)

def test_total_with_coupon_and_member_shipping():
    c = Cart()
    c.add_item("item", 1000, quantity=1)  # subtotal 1000 free shipping
    # apply coupon SAVE10 -> 900
    total_expected = round(900 + 0, 2)
    assert c.total(coupon="SAVE10") == total_expected
    # test member half shipping when not free
    c.remove_item("item")
    c.add_item("item", 100, quantity=1)  # subtotal 100 -> 60 shipping
    total_expected = round(apply_discount(100, 20) + 30, 2)
    assert c.total(member=True, coupon="SAVE20") == total_expected

# ---------- empty cart ----------------------------------------------

def test_empty_cart_total():
    c = Cart()
    assert c.total() == 0.0
    assert c.total(coupon="SAVE10") == 0.0
