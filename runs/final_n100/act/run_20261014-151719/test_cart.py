import pytest
from cart import apply_discount, parse_coupon, Cart, bulk_discount_percent, shipping_fee

# --- Tests for apply_discount -------------------------------------------------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0
    # rounding to two decimals
    assert apply_discount(123.456, 10) == round(123.456 * 0.90, 2)

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --- Tests for parse_coupon ---------------------------------------------------

def test_parse_coupon_valid_codes():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe30   ") == 30

@ pytest.mark.parametrize("code", ["SAVEX", "123", "", "SAVE0", "SAVE51", "NOTVALID"])
def test_parse_coupon_invalid_codes(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- Tests for bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

# --- Tests for shipping_fee ---------------------------------------------------

def test_shipping_fee():
    # subtotal < 1000: fee 60, member half
    assert shipping_fee(50) == 60
    assert shipping_fee(500, member=True) == 30
    # free over 1000
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500, member=False) == 0

# --- Tests for Cart class -----------------------------------------------------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item("apple", 1.5, quantity=3)
    cart.add_item("banana", 0.75)
    items = cart.items()
    assert isinstance(items, dict)
    assert len(items) == 2
    assert items["apple"] == 3
    assert items["banana"] == 1


def test_cart_remove_and_subtotal():
    cart = Cart()
    cart.add_item("cherry", 0.2, quantity=10)
    # 10 * 0.2 = 2.0
    assert cart.subtotal() == 2.0
    # remove 5 cherries
    cart.remove_item("cherry", quantity=5)
    assert cart.subtotal() == 1.0
    # removing more than present removes all remaining items
    cart.remove_item("cherry", quantity=10)
    assert cart.subtotal() == 0.0


def test_cart_total_with_member_and_coupon():
    cart = Cart()
    cart.add_item("item1", 100)
    cart.add_item("item2", 200, quantity=2)  # subtotal = 500
    total_no_discount = cart.total(member=False, coupon=None)
    assert total_no_discount == 500 + shipping_fee(500)

    total_coupon = cart.total(member=True, coupon="SAVE10")
    discounted_subtotal = apply_discount(500, 10)
    expected_total = discounted_subtotal + shipping_fee(discounted_subtotal, member=True)
    assert total_coupon == expected_total

# Test that coupon parsing errors propagate through Cart.total

def test_cart_invalid_coupon():
    cart = Cart()
    cart.add_item("widget", 50)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")
