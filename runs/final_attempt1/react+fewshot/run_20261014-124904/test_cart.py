import pytest
import cart

# ---------- apply_discount ---------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ---------

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ---------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe5") == 5

@pytest.mark.parametrize("code", ["SAVE0", "SAVEXX", "SAVED", "NOPE10", "save51", "sAVE-1", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------

def test_shipping_fee_cases():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    assert cart.shipping_fee(50, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", unit_price=100, quantity=2)
    assert c.subtotal() == 200.0
    c.add_item("apple", unit_price=100, quantity=3)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == 500.0

def test_add_item_bulk_discount():
    c = cart.Cart()
    c.add_item("banana", unit_price=10, quantity=15)
    discounted_unit = 10 * (1 - 0.05)
    assert c.subtotal() == round(discounted_unit * 15, 2)

def test_add_item_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", unit_price=-5, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pear", unit_price=5, quantity=0)

def test_remove_item():
    c = cart.Cart()
    c.add_item("orange", 50, 3)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 1}
    c.remove_item("orange", 1)
    assert "orange" not in c.items()

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# total calculation: subtotal, coupon, shipping

def test_total_no_coupon_member_fee_free():
    c = cart.Cart()
    c.add_item("item", 1000, 1)
    assert c.total(member=True) == 1000.00

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, 5)
    subtotal = 200 * 5
    coupon_discount = subtotal * 0.10
    after_coupon = subtotal - coupon_discount
    shipping = cart.shipping_fee(after_coupon)
    total_expected = round(after_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == total_expected

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("thing", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
