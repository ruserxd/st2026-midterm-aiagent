import pytest
import cart

# Helper for approximate equality

def approx(val, target, tol=1e-9):
    return abs(val - target) < tol

# ---------- apply_discount tests ----------

@ pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# ValueError cases for price and percent
@ pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@ pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (250,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@ pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------
@ pytest.mark.parametrize("code,result", [
    ("SAVE10",10),
    ("save20 ",20),
    ("  SaVe50  ",50),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

@ pytest.mark.parametrize("code", ["SAV10","SAVE0","SAVE51","ABC12","SAVE-5","" ])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@ pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

@pytest.fixture
def empty_cart():
    return cart.Cart()

@ pytest.mark.parametrize("name,price,qty", [
    ("apple", 100, 1),
    ("banana", 50.5, 3),
])
def test_add_item(empty_cart, name, price, qty):
    empty_cart.add_item(name, price, qty)
    assert empty_cart.items() == {name: qty}
    # adding same item increases quantity
    if qty == 1:
        empty_cart.add_item(name, price, 2)
        assert empty_cart.items()[name] == 3

# Adding with different unit price raises ValueError
@ pytest.mark.parametrize("name", ["orange"]) 
def test_add_item_diff_price(empty_cart, name):
    empty_cart.add_item(name, 10, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item(name, 12, 1)

# Invalid quantity or price raise ValueError
@ pytest.mark.parametrize("price,qty", [(-5,1),(10,-2),(10,0)])
def test_add_item_errors(empty_cart, price, qty):
    with pytest.raises(ValueError):
        empty_cart.add_item("item", price, qty)

# remove_item tests
@ pytest.mark.parametrize("name,price,qty", [
    ("tshirt", 200, 5),
])
def test_remove_item(empty_cart, name, price, qty):
    empty_cart.add_item(name, price, qty)
    empty_cart.remove_item(name, 2)
    assert empty_cart.items()[name] == qty-2
    # remove remaining
    empty_cart.remove_item(name, qty-2)
    assert name not in empty_cart.items()

# Removing non-existent item raises KeyError
@ pytest.mark.parametrize("name", ["nonexistent"]) 
def test_remove_item_keyerror(empty_cart, name):
    with pytest.raises(KeyError):
        empty_cart.remove_item(name, 1)

# subtotal calculation tests
@ pytest.mark.parametrize("items,expected_subtotal", [
    ({},0.0),
    ({"item": (20,1)},20.0), # unit price, qty
    ({"bulk": (10,10)}, 95.0), # 5% discount on 10 items: 10*10=100-5=95
    ({"bulk2":(30,50)}, 1350.0), # 10% off: 1500-150=1350
])
def test_subtotal_calculation(empty_cart, items, expected_subtotal):
    for name,(price,qty) in items.items():
        empty_cart.add_item(name, price, qty)
    assert approx(empty_cart.subtotal(), expected_subtotal)

# total calculation tests
@ pytest.mark.parametrize("items,coupon,member,expected_total", [
    ({}, None, False, 0.0),
    ({"x":(100,2)}, None, False, 200.0), # no shipping (subtotal<1000)
    ({"x":(500,3)}, None, True, 1500.0+30.0),
    ({"y":(100,5)}, "SAVE10", False, 450.0 -45.0 +60.0), # subtotal 500, coupon 10%, fee 60
])
def test_total_calculation(empty_cart, items, coupon, member, expected_total):
    for name,(price,qty) in items.items():
        empty_cart.add_item(name, price, qty)
    assert approx(empty_cart.total(member=member, coupon=coupon), expected_total)

# total with invalid coupon raises ValueError
@ pytest.mark.parametrize("items,coupon", [
    ({"a":(100,1)}, "ABC10"),
])
def test_total_invalid_coupon(empty_cart, items, coupon):
    for name,(price,qty) in items.items():
        empty_cart.add_item(name, price, qty)
    with pytest.raises(ValueError):
        empty_cart.total(coupon=coupon)
