import pytest
import cart

# ---------- helpers for expected values from spec ----------

def exp_apply_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# tests for standalone functions

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(50, 0) == 50.0
    assert cart.apply_discount(99.99, 33) == round(99.99 * 0.67, 2)

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["save0", "save51", "SAVEXX", "100"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee

def test_shipping_fee_non_member():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

@ pytest.mark.parametrize("member", [True, False])
def test_shipping_fee_member(member):
    if member:
        assert cart.shipping_fee(999, member=True) == 30
    else:
        assert cart.shipping_fee(999, member=False) == 60

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

@ pytest.mark.parametrize("name,unit_price,quantity", [
    ("apple", 1.00, 3),
    ("banana", 0.50, 5),
])
def test_add_item(name, unit_price, quantity):
    c = cart.Cart()
    c.add_item(name, unit_price, quantity)
    assert c.items()[name] == quantity

# adding same item increases quantity and checks price consistency

def test_add_same_item_increases_quantity():
    c = cart.Cart()
    c.add_item("milk", 2.00, 1)
    c.add_item("milk", 2.00, 2)
    assert c.items()["milk"] == 3

# adding same item with different price raises ValueError

def test_add_same_item_different_price():
    c = cart.Cart()
    c.add_item("bread", 1.50, 1)
    with pytest.raises(ValueError):
        c.add_item("bread", 2.00, 1)

# invalid quantity or price raise ValueError

def test_add_invalid_price_or_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("eggs", -1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("eggs", 1.0, 0)

# remove_item

def test_remove_item():
    c = cart.Cart()
    c.add_item("orange", 0.80, 3)
    c.remove_item("orange", 2)
    assert c.items()["orange"] == 1

# removing all quantity removes the item

def test_remove_all_quantity():
    c = cart.Cart()
    c.add_item("pear", 0.90, 2)
    c.remove_item("pear", 2)
    assert "pear" not in c.items()

# remove more than existing raises KeyError or removes item if quantity reaches zero? spec says removed when <=0, but removing a non‑existent item raises KeyError.

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal calculations including bulk discount and rounding

def test_subtotal_with_bulk_discount_and_rounding():
    c = cart.Cart()
    # 5 items -> no discount
    c.add_item("itemA", 10.0, 5)
    # 10 items -> 5% discount on this item only
    c.add_item("itemB", 20.0, 10)
    # 100 items -> 15% discount on this item only
    c.add_item("itemC", 30.0, 100)
    expected = round(10.0*5 + 20.0*10*(1-0.05) + 30.0*100*(1-0.15), 2)
    assert c.subtotal() == expected

# total calculation with coupon and shipping fee

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 250.0, 4)   # subtotal = 1000 (no discount)
    # subtotal after coupon 10% -> 900
    total = c.total(member=False, coupon="SAVE10")
    expected = round(900 + cart.shipping_fee(900), 2)
    assert total == expected

# total for empty cart is zero and no shipping

def test_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0

# coupon invalid raises ValueError in total

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
