import pytest
import cart

# Helper to create a cart with some items

def make_simple_cart():
    c = cart.Cart()
    c.add_item("apple", 10, quantity=5)   # bulk discount applies: 5% for 5<10 -> no discount
    return c

# --- tests for parse_coupon --------------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe5  ") == 5

@ pytest.mark.parametrize("code", ["", "A123", "SAVExx", "SAVE0", "SAVE51", 123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- tests for bulk_discount_percent -----------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.5)

# --- tests for shipping_fee --------------------------------------------

def test_shipping_fee_non_member():
    # subtotal < 1000 -> fee 60
    assert cart.shipping_fee(999) == 60
    # free shipping threshold not defined; spec says >=1000 free
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

@ pytest.mark.parametrize("subtotal,expected", [(0,30),(500,30)])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

# --- tests for Cart subtotal --------------------------------------------

def test_cart_subtotal_basic():
    c = cart.Cart()
    c.add_item("x", 20, quantity=3)
    # bulk discount 5% because quantity 3<10 -> none
    assert c.subtotal() == 60.0

@ pytest.mark.parametrize(
    "name,price,qty,expected",
    [
        ("a", 100, 5, 500),   # no bulk discount
        ("b", 200, 10, 190),  # 5% discount -> 200*10=2000 *0.95=1900
        ("c", 50, 55, 2375),  # 10% discount: 2750*0.9=2475? Wait compute
    ],
)
def test_cart_subtotal_bulk(name, price, qty, expected):
    c = cart.Cart()
    c.add_item(name, price, quantity=qty)
    assert c.subtotal() == round(price * qty * (1 - cart.bulk_discount_percent(qty)/100), 2)

# --- tests for Cart total -----------------------------------------------

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0


def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("x", 50, quantity=2)  # subtotal 100
    # no coupon, shipping fee 60 -> total 160
    assert c.total() == round(100 + 60, 2)


def test_cart_total_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("x", 200, quantity=5)   # subtotal 1000
    # discount 10% via coupon -> 900, shipping fee should be on discounted amount (900>=1000? no) so 60
    assert c.total(coupon="SAVE10") == round(900 + 60, 2)

# Test that shipping is computed on subtotal after coupon but not on original subtotal

def test_cart_total_shipping_on_discounted_amount():
    c = cart.Cart()
    c.add_item("x", 200, quantity=5)   # subtotal 1000
    # free shipping if >=1000, but after discount may be below threshold
    assert c.total(coupon="SAVE20") == round(800 + 60, 2)

# --- test that remove_item reduces quantity and removes when zero ---

def test_remove_item():
    c = cart.Cart()
    c.add_item("x", 10, quantity=3)
    c.remove_item("x", quantity=1)
    assert c.items()["x"] == 2
    c.remove_item("x", quantity=2)
    assert "x" not in c.items()

# --- test that adding same item with different price raises error ---

def test_add_same_item_different_price():
    c = cart.Cart()
    c.add_item("x", 10, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("x", 12, quantity=1)

# Additional tests to expose implementation bugs: shipping_fee constants missing

def test_shipping_fee_constants_missing():
    # If constants are undefined, the function will raise NameError
    with pytest.raises(NameError):
        cart.shipping_fee(500)
