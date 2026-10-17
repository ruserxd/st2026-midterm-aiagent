import pytest
import cart

# ---------- basic functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 33) == 67.0

@ pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk discount ----------

def test_bulk_discount():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

# ---------- coupon parsing ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe50 ") == 50

@ pytest.mark.parametrize("code", ["SAVE0", "SAVExx", "100", ""]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping fee ----------

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("sub", [-1, -50.5])
def test_shipping_negative(sub):
    with pytest.raises(ValueError):
        cart.shipping_fee(sub)

# ---------- Cart class tests ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=5)
    assert c.items()["apple"] == 5
    # adding same item increases quantity
    c.add_item("apple", 1.00, quantity=2)
    assert c.items()["apple"] == 7
    with pytest.raises(ValueError):
        c.add_item("apple", 0.90)
    with pytest.raises(KeyError):
        c.remove_item("banana")

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("item", 10, quantity=9)
    assert c.subtotal() == 90.0
    c.add_item("item", 10, quantity=1)
    # qty now 10 -> 5% discount
    assert c.subtotal() == round(100 * 0.95, 2)

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=3)
    subtotal = 600
    total_no_coupon = c.total(member=False)
    assert total_no_coupon == round(subtotal + 60, 2)
    total_with_coupon = c.total(coupon="SAVE10")
    discounted = subtotal * 0.90
    expected = round(discounted + 60, 2)
    assert total_with_coupon == expected
