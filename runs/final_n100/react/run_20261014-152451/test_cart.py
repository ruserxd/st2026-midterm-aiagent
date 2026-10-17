import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Tests for apply_discount

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [ -1 , -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# Tests for bulk_discount_percent

def test_bulk_discount_percent_breakpoints():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# Tests for parse_coupon

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("   SAVE5   ") == 5

@ pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "123SAVE10", "SAVE-10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee

def test_shipping_fee_breakpoints():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

# Non-member vs member fee

def test_shipping_fee_member():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Tests for Cart class

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # shipping fee for empty cart (subtotal 0, non-member)

# Adding items and subtotal calculation

def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=3)  # total 300
    assert c.items()["apple"] == (100, 3)
    assert c.subtotal() == 300

# Removing items

def test_cart_remove():
    c = Cart()
    c.add_item("banana", unit_price=50, quantity=5)
    c.remove_item("banana", quantity=2)  # left 3
    assert c.items()["banana"] == (50, 3)
    c.remove_item("banana", quantity=3)  # item removed
    assert "banana" not in c.items()

# Bulk discount application in total

def test_cart_total_bulk_discount():
    c = Cart()
    c.add_item("widget", unit_price=20, quantity=10)  # 200 subtotal
    # bulk discount 5% -> 190 after discount, then shipping 60 => 250
    assert c.total() == 250

# Coupon application

def test_cart_total_coupon():
    c = Cart()
    c.add_item("gadget", unit_price=50, quantity=1)
    # subtotal 50, no bulk discount
    # apply coupon SAVE10 -> 45
    assert c.total(coupon="SAVE10") == 105  # 45 + 60 shipping

# Member shipping and total

def test_cart_total_member_shipping():
    c = Cart()
    c.add_item("item", unit_price=200, quantity=6)  # subtotal 1200 >1000 => free shipping
    assert c.total(member=True) == 1200

# Edge: coupon with discount leading to zero after bulk

def test_cart_total_coupon_no_bulks():
    c = Cart()
    c.add_item("toy", unit_price=10, quantity=50)  # subtotal 500, bulk 10% -> 450
    assert c.total(coupon="SAVE10") == 405  # 450-45 + 60 shipping

# Combined member and coupon

def test_cart_total_member_coupon():
    c = Cart()
    c.add_item("item", unit_price=200, quantity=6)  # subtotal 1200
    assert c.total(member=True, coupon="SAVE20") == 960  # 1200 -20% = 960, no shipping

# Ensure ValueError on negative unit price or quantity in add_item

def test_cart_add_negative():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", unit_price=-10, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("zeroqty", unit_price=10, quantity=0)

# Ensure remove_item raises if item not present or removing more than exists

def test_cart_remove_errors():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")
    c.add_item("foo", 5, quantity=1)
    with pytest.raises(ValueError):
        c.remove_item("foo", quantity=2)
