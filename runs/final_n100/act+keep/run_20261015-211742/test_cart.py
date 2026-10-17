import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent",[( -1,10),(100,-5),(100,105)]
)
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        apply_discount(price,percent)

# --- bulk_discount_percent -------------------------------------------

def test_bulk_discount_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty",[0,-5,3.2])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(int(qty)) if isinstance(qty,int) else bulk_discount_percent(qty)

# --- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("   SaVe50  ") == 50

@ pytest.mark.parametrize("code",["SAVEX","saves"," SAVE51 ","100"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500, False) == 60
    assert shipping_fee(500, True) == 30
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0

@ pytest.mark.parametrize("subtotal",[-1,-5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart class --------------------------------------------------------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, quantity=2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 1.0, quantity=3)
    assert c.items() == {"apple": 5}
    c.add_item("banana", 0.5)
    assert c.items() == {"apple": 5, "banana": 1}


def test_cart_add_error_on_price_mismatch():
    c = Cart()
    c.add_item("orange", 2.0)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.0)

@ pytest.mark.parametrize("qty",[0,-1])
def test_cart_add_invalid_qty(qty):
    with pytest.raises(ValueError):
        Cart().add_item("pear", 1.5, quantity=qty)

@ pytest.mark.parametrize("price",[-1])
def test_cart_add_invalid_price(price):
    with pytest.raises(ValueError):
        Cart().add_item("pear", price)

# --- remove_item -----------------------------------------------------

def test_remove_item_basic():
    c = Cart()
    c.add_item("mango", 1.0, quantity=5)
    c.remove_item("mango", quantity=2)
    assert c.items() == {"mango":3}
    c.remove_item("mango", quantity=3)
    assert "mango" not in c.items()


def test_remove_item_zero_or_less_removes():
    c = Cart()
    c.add_item("peach", 1.0, quantity=2)
    c.remove_item("peach", quantity=5)
    assert c.items() == {}

@ pytest.mark.parametrize("missing",["orange","banana"])
def test_remove_nonexistent_key(missing):
    with pytest.raises(KeyError):
        Cart().remove_item(missing)

# --- subtotal ---------------------------------------------------------

def test_subtotal_calculation():
    c = Cart()
    c.add_item("apple", 1.0, quantity=3)  # qty=3 -> 5% discount
    assert round(c.subtotal(),2) == round(1.0*3*(1-0.05),2)
    c.add_item("banana", 0.5, quantity=10)  # qty=10 -> 5% discount
    expected = round((1.0*3*(1-0.05)) + (0.5*10*(1-0.05)),2)
    assert round(c.subtotal(),2) == expected

# --- total ------------------------------------------------------------

def test_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("orange", 20.0, quantity=5)
    subtotal = 100.0
    assert round(c.subtotal(),2) == subtotal
    coupon_percent = parse_coupon("SAVE10")
    total_after_coupon = subtotal * (1-coupon_percent/100)
    shipping = shipping_fee(total_after_coupon)
    expected_total = round(total_after_coupon + shipping,2)
    assert c.total(coupon="SAVE10") == expected_total


def test_total_member_free_shipping():
    c = Cart()
    c.add_item("item", 200.0, quantity=6)  # subtotal 1200 no bulk discount
    total = round(1200 + shipping_fee(1200),2)
    assert total == 1200
    assert c.total(member=True) == 1200


def test_total_empty_cart():
    c = Cart()
    assert c.total() == 0
    assert c.total(coupon="SAVE10") == 0

# --- error handling in total ------------------------------------------

def test_total_invalid_coupon_raises():
    c = Cart()
    c.add_item("item",1)
    with pytest.raises(ValueError):
        c.total(coupon="invalid")
