import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (0, 0),   # zero price, zero percent -> 0
    (100, 0), # no discount
    (50, 100),# full discount
])
def test_apply_discount_various(price, percent):
    expected = round(price * (1 - percent / 100.0), 2)
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", ["abc", -5, 105, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --------- bulk_discount_percent ----------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(250) == 15

@pytest.mark.parametrize("qty", [0, -1, -10])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# --------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon(" SAVE5 ") == 5

@pytest.mark.parametrize("code", ["save0", "save51", "abc10", "SA V15", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --------- Cart class ----------

def test_cart_initially_empty():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0


def test_add_item_and_subtotal_no_discount():
    cart = Cart()
    cart.add_item("apple", 2.00, quantity=3)
    assert cart.items() == {"apple": 3}
    # No bulk discount for qty 3 -> 6.0
    assert cart.subtotal() == 6.0


def test_add_multiple_items_and_bulk_discount():
    cart = Cart()
    cart.add_item("banana", 1.00, quantity=12)   # qty >=10 =>5%
    cart.add_item("orange", 3.00, quantity=55)   # qty >=50 =>10%
    # banana subtotal: 12*1=12 -> 5% off = 11.40
    # orange subtotal: 55*3=165 -> 10% off = 148.5
    assert cart.subtotal() == round(11.4 + 148.5, 2)


def test_remove_item_and_quantity_update():
    cart = Cart()
    cart.add_item("milk", 1.50, quantity=5)
    cart.remove_item("milk", quantity=3)
    assert cart.items() == {"milk": 2}
    # Remove remaining
    cart.remove_item("milk", quantity=2)
    assert cart.items() == {}


def test_remove_nonexistent_item():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item("nonexist")


def test_total_with_coupon_and_shipping_member():
    cart = Cart()
    cart.add_item("widget", 100, quantity=10)  # qty 10 ->5% bulk
    subtotal = cart.subtotal()  # 1000 -5% => 950.0
    total_without_couponship = subtotal + shipping_fee(subtotal)
    # apply coupon SAVE10: reduce by 10%
    after_coupon = apply_discount(total_without_couponship, 10)
    expected_total = round(after_coupon + shipping_fee(after_coupon), 2)
    assert cart.total(member=True, coupon="SAVE10") == expected_total


def test_total_empty_cart_no_shipping():
    cart = Cart()
    assert cart.total() == 0

# Edge: coupon invalid should raise ValueError when calling total

def test_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("test", 10, quantity=1)
    with pytest.raises(ValueError):
        cart.total(coupon="invalid")

# Edge: adding item with mismatched unit price raises ValueError

def test_add_item_price_mismatch():
    cart = Cart()
    cart.add_item("item", 5.0, quantity=2)
    with pytest.raises(ValueError):
        cart.add_item("item", 4.99, quantity=1)

# Edge: adding item with negative unit price or zero quantity raises ValueError

def test_add_invalid_unit_price_or_quantity():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("badprice", -1, quantity=1)
    with pytest.raises(ValueError):
        cart.add_item("badqty", 1, quantity=0)

# Edge: remove item more than existing quantity removes it entirely

def test_remove_more_than_existing():
    cart = Cart()
    cart.add_item("excess", 2.0, quantity=3)
    cart.remove_item("excess", quantity=5)  # should drop to 0 and remove
    assert "excess" not in cart.items()
