import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 99.99 with 10% -  -> 89.991 rounded to 2 decimals
    assert apply_discount(99.99, 10) == round(99.99 * 0.9, 2)

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_nonpositive():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-10)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon(" SAVE5") == 5
    assert parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["SAVE", "SAVE0", "SAVE51", "SAVExx"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_for_high_subtotal():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.50) == 0

def test_shipping_fee_regular_and_member():
    # subtotal < 1000
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(0) == 60

@ pytest.mark.parametrize("subtotal", [-1])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class behavior ----------

def test_cart_add_and_subtotal():
    cart = Cart()
    cart.add_item("apple", 2.0, quantity=3)
    assert cart.items() == [("apple", 2.0, 3)]
    assert cart.subtotal() == 6.0

def test_cart_remove_and_quantity():
    cart = Cart()
    cart.add_item("banana", 1.5, quantity=5)
    cart.remove_item("banana", quantity=2)
    assert cart.items() == [("banana", 1.5, 3)]

def test_cart_remove_excess_quantity():
    cart = Cart()
    cart.add_item("orange", 0.5, quantity=2)
    cart.remove_item("orange", quantity=5)  # should remove item entirely
    assert cart.items() == []

def test_cart_total_without_coupon_and_no_member():
    cart = Cart()
    cart.add_item("widget", 10.0, quantity=1)
    # subtotal 10, shipping 60 -> total 70
    assert cart.total(member=False) == 70.0

def test_cart_total_with_coupon_and_member():
    cart = Cart()
    cart.add_item("gadget", 50.0, quantity=2)  # subtotal 100
    # coupon SAVE10 reduces to 90, shipping 60 -> total 150
    assert cart.total(member=True, coupon="SAVE10") == 150.0

def test_cart_total_empty_cart():
    cart = Cart()
    assert cart.total() == 0.0

def test_cart_total_invalid_coupon_raises():
    cart = Cart()
    cart.add_item("item", 20)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")
