import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

# rounding: price=101, percent=15 -> 85.85

def test_apply_discount_rounding():
    assert apply_discount(101, 15) == round(101 * (1 - 0.15), 2)

@ pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("q", [0, -3])
def test_bulk_discount_invalid(q):
    with pytest.raises(ValueError):
        bulk_discount_percent(q)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE10 ") == 10
    assert parse_coupon("SaVe50") == 50
    assert parse_coupon(" SaVe1 ") == 1

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAF10", "", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200) == 0

@ pytest.mark.parametrize("subtotal", [10, -5])
def test_shipping_fee_invalid(subtotal):
    if subtotal < 0:
        with pytest.raises(ValueError):
            shipping_fee(subtotal)

# member half fee
assert shipping_fee(999.99, member=True) == 30
assert shipping_fee(1001, member=True) == 0

# ---------- Cart class ------------------------------------------------------

def test_cart_basic_operations():
    c = Cart()
    assert c.items() == []
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

    c.add_item("apple", unit_price=100, quantity=3)
    c.add_item("banana", unit_price=50, quantity=2)
    # subtotal = 3*100 + 2*50 = 350
    assert c.subtotal() == 350.0

    # total without shipping: subtotal 350 < 1000 -> shipping 60
    assert c.total() == round(350 + 60, 2)

    # coupon discount
    assert c.total(coupon="SAVE10") == round((350 * 0.90) + 60, 2)

    # member pays half shipping
    assert c.total(member=True) == round(350 + 30, 2)
    assert c.total(member=True, coupon="SAVE10") == round((350 * 0.90) + 30, 2)

    # remove items
    c.remove_item("apple", quantity=1)  # now apples=2
    assert c.subtotal() == 250.0

    c.remove_item("banana", quantity=5)  # removes all bananas
    assert len(c.items()) == 1
    assert c.items()[0]["name"] == "apple"
    assert c.total() == round(200 + 60, 2)

# test invalid coupon in Cart.total

def test_cart_invalid_coupon():
    c = Cart()
    c.add_item("item", unit_price=100)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# test bulk discount applied per item? (spec unclear; not testing)

if __name__ == "__main__":
    pytest.main(["-q"])
