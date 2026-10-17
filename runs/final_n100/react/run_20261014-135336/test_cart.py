import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Test apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

def test_apply_discount_zero_and_full():
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(80, 100) == 0.0

@ pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(50, percent)

# ---------- Test bulk_discount_percent ----------

def test_bulk_discount_quantities():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(15) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(75) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Test parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save15 ") == 15
    assert parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize(
    "code",
    ["", "SAVE0", "SAVE51", "NOTVALID", "SAVE-5", "SAVEXX", "  "]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Test shipping_fee ----------

def test_shipping_fee_standard_and_free():
    assert shipping_fee(999) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(5000) == 0

@ pytest.mark.parametrize("subtotal", [50, -1])
def test_shipping_fee_invalid(subtotal):
    if subtotal < 0:
        with pytest.raises(ValueError):
            shipping_fee(subtotal)

# Member discounts

def test_member_shipping():
    assert shipping_fee(200, member=True) == 30

# ---------- Test Cart class behavior ----------

def test_cart_initialization_and_add_remove():
    cart = Cart()
    # Initially empty
    assert cart.items() == {}
    # Add item
    cart.add_item("apple", 2.5, quantity=3)
    assert cart.items() == {"apple": (2.5, 3)}
    # Adding same item increases quantity
    cart.add_item("apple", 2.5, quantity=2)
    assert cart.items()["apple"] == (2.5, 5)
    # Add different item
    cart.add_item("banana", 1.0)
    assert "banana" in cart.items()

    # Remove part of quantity
    cart.remove_item("apple", quantity=2)
    assert cart.items()["apple"] == (2.5, 3)

    # Remove entire quantity -> item removed
    cart.remove_item("apple", quantity=3)
    assert "apple" not in cart.items()

    # Removing more than present should raise error
    with pytest.raises(ValueError):
        cart.remove_item("banana", quantity=5)

# Subtotal calculation

def test_cart_subtotal():
    c = Cart()
    c.add_item("book", 15.0, 2)  # $30
    c.add_item("pen", 1.5, 3)   # $4.5
    assert c.subtotal() == 34.5

# Total calculation with discounts and shipping

def test_cart_total_no_discounts():
    c = Cart()
    c.add_item("item", 100)
    assert c.total() == 160.0  # $100 + $60 shipping

def test_cart_total_member_and_coupon():
    c = Cart()
    c.add_item("big", 600, 2)   # $1200 subtotal
    # Member gets free shipping and bulk discount of 15%
    total = c.total(member=True)
    expected_subtotal = apply_discount(1200, bulk_discount_percent(2))  # no bulk discount because qty<10
    # but our logic: bulk_discount_percent expects quantity per item; here each quantity is 2.
    # So subtotal remains 1200. shipping fee 0 for member >$1000
    assert total == expected_subtotal + 0

def test_cart_total_with_coupon():
    c = Cart()
    c.add_item("tshirt", 20, 10)  # 200 subtotal
    # bulk discount 5%
    discounted_subtotal = apply_discount(200, 5)
    total_without_shipping = discounted_subtotal * (1 - 0.10)  # coupon SAVE10
    total = c.total(coupon="SAVE10")
    assert round(total, 2) == round(total_without_shipping + shipping_fee(200), 2)
