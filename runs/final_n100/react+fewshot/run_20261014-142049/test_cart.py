import pytest
import cart

# --- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent", [
    (0, 0),
    (100, 50),
    (123.45, 33)
])
def test_apply_discount_various(price, percent):
    expected = round(price * (1 - percent / 100), 2)
    assert cart.apply_discount(price, percent) == expected

# boundary checks for errors
with pytest.raises(ValueError):
    cart.apply_discount(-5, 10)
with pytest.raises(ValueError):
    cart.apply_discount(50, -1)
with pytest.raises(ValueError):
    cart.apply_discount(50, 101)

# --- bulk_discount_percent ------------------------------------------

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-3)

# --- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("   SaVe30   ") == 30

with pytest.raises(ValueError):
    cart.parse_coupon("SAVEXX")

with pytest.raises(ValueError):
    cart.parse_coupon("SAVE0")

with pytest.raises(ValueError):
    cart.parse_coupon("SAVE51")

# --- shipping_fee ----------------------------------------------------

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(0, member=False) == 60

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# --- Cart operations -----------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # add same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}
    # adding new item
    c.add_item("banana", 0.50, 4)
    assert c.items() == {"apple": 5, "banana": 4}

    with pytest.raises(ValueError):
        c.add_item("orange", -1, 1)          # negative price
    with pytest.raises(ValueError):
        c.add_item("orange", 0.30, 0)        # non‑positive quantity

    # test that unit_price must match existing
    c.add_item("bread", 2.00, 1)
    with pytest.raises(ValueError):
        c.add_item("bread", 2.50, 1)

# test remove
c = cart.Cart()
c.add_item("milk", 3.00, 5)
# remove less than quantity
c.remove_item("milk", 2)
assert c.items() == {"milk": 3}
# remove exactly remaining - item removed
c.remove_item("milk", 3)
assert c.items() == {}
with pytest.raises(KeyError):
    c.remove_item("juice", 1)   # not present

# --- Cart subtotal ---------------------------------------------------
def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("item", 10.00, 9)
    assert c.subtotal() == 90.0     # no bulk discount

def test_cart_subtotal_with_bulk():
    c = cart.Cart()
    c.add_item("small", 5.00, 10)   # 5% off
    c.add_item("medium", 2.00, 50)  # 10% off
    c.add_item("large", 1.00, 100)  # 15% off
    expected = round(5*10*(0.95)+2*50*(0.90)+1*100*(0.85), 2)
    assert c.subtotal() == expected

# --- Cart total -----------------------------------------------------
def test_cart_total_basic():
    c = cart.Cart()
    c.add_item("toy", 20.00, 3)   # no bulk discount
    # subtotal 60, no coupon, member False => shipping 60
    assert c.total() == round(60+60, 2)

# coupon reduces before shipping
c = cart.Cart()
c.add_item("gift", 100.0, 1)
subtotal = 100.0
expected_total = round(90 + 60, 2)  # after SAVE10
assert c.total(coupon="SAVE10") == expected_total

# member gets half shipping
c = cart.Cart()
c.add_item("book", 200.0, 1)
expected_member = round(200 + 30, 2)
assert c.total(member=True) == expected_member

# empty cart cost 0 (no shipping)
c = cart.Cart()
assert c.total() == 0.0
