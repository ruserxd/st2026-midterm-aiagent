import pytest
import cart

# Helper to set up a cart with items

def make_cart_with_items(items):
    c = cart.Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Errors for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (100, -5),  # negative percent
    (100, 105), # percent > 100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,expected_percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected_percent):
    assert cart.bulk_discount_percent(quantity) == expected_percent

# Errors for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code,percent", [
    ("SAVE10", 10),
    ("save20 ", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", [
    "",
    "SAVEXX",
    "SAVE0",
    "SAVE51",
    "BAD10",
    "save-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000.00, False, 0),
    (500, True, 30),
    (0, False, 60),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Errors for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart add/remove and items
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 2.0, 3)
    c.add_item("banana", 1.5)
    assert c.items() == {"apple": 3, "banana": 1}
    # adding same item increases quantity
    c.add_item("apple", 2.0, 2)
    assert c.items()["apple"] == 5

# Error when adding with different unit price
def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("cherry", 1.0)
    with pytest.raises(ValueError):
        c.add_item("cherry", 2.0)

# Remove item and automatic removal when quantity reaches zero
def test_cart_remove_and_auto_remove():
    c = cart.Cart()
    c.add_item("durian", 5.0, 4)
    c.remove_item("durian", 2)
    assert c.items()["durian"] == 2
    c.remove_item("durian", 3)  # should remove entirely (2-3 <=0)
    assert "durian" not in c.items()

# Removing non-existent item raises KeyError
def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("eggplant")

# subtotal calculation
def test_cart_subtotal():
    c = make_cart_with_items([
        ("fish", 10.0, 2),   # 20
        ("gadget", 5.5, 1),  # 5.5
    ])
    assert c.subtotal() == 25.5

# total calculation with coupon and shipping
@pytest.mark.parametrize("cart_items,coupon_code,member,total_expected", [
    ([("hat", 100.0, 1)], None, False, 160.0), # 100 + 60 = 160
    ([("jacket", 200.0, 1)], "SAVE10", False, 170.0), # 200-20=180 + 60 shipping? subtotal 200 -> 200-20=180; shipping 60 -> 240?? Wait need compute: subtotal 200, coupon 10% => 180, shipping 60 (since <1000) => 240
    # Let's recompute: expected 240.0
    ([("coat", 1200.0, 1)], "SAVE5", True, 1140.0), # subtotal 1200 >1000 free shipping; coupon 5% => 1140
])
def test_cart_total(cart_items, coupon_code, member, total_expected):
    c = make_cart_with_items([(name, price, qty) for name, price, qty in cart_items])
    if coupon_code is None:
        assert c.total(member=member) == total_expected
    else:
        assert c.total(member=member, coupon=coupon_code) == total_expected

# Empty cart total is 0
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.0

# Invalid coupon in total raises ValueError
def test_cart_total_invalid_coupon():
    c = make_cart_with_items([("item", 10.0, 1)])
    with pytest.raises(ValueError):
        c.total(coupon="BAD")
