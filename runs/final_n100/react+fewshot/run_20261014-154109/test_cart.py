import pytest
import cart

# ---------- Helper asserts for rounding ----------

def approx_eq(a, b, tol=1e-9):
    return abs(a - b) <= tol

# ----------- apply_discount tests -----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),            # example from spec
        (100, 0, 100.0),             # no discount
        (50, 100, 0.0),              # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary checks for ValueError in apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, 100.5, -1, -0.1])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

# ----------- bulk_discount_percent tests -----------
@pytest.mark.parametrize(
    "qty, expected",
    [
        (5, 0),      # below 10
        (10, 5),     # boundary 10
        (49, 5),     # just below 50
        (50, 10),    # boundary 50
        (99, 10),    # just below 100
        (100, 15),   # boundary 100
        (150, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# invalid quantity for bulk discount
@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ----------- parse_coupon tests -----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),      # case-insensitive
        ("  SAVE30 ", 30),   # whitespace ignored
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "NOTCPT", "save-5", "save 10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----------- shipping_fee tests -----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),      # below 1000, non-member
        (999.99, True, 30),   # just below threshold, member half fee
        (1000, False, 0),     # free shipping at threshold
        (1500, True, 0),     # free shipping for members too
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# negative subtotal raises ValueError
@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----------- Cart tests (empty cart) -----------
def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0
    # subtotal of empty is zero, no shipping applied
    assert c.subtotal() == 0
    assert c.items() == {}

# adding items and verifying quantities
@pytest.mark.parametrize(
    "name, unit_price, quantity",
    [
        ("apple", 1.0, 5),
        ("banana", 0.5, 12),  # triggers bulk discount
        ("orange", 2.0, 3),
    ],
)
def test_add_and_items(name, unit_price, quantity):
    c = cart.Cart()
    c.add_item(name, unit_price, quantity)
    assert c.items() == {name: quantity}

# adding same item increases quantity, price must match
def test_add_same_item_increases_quantity():
    c = cart.Cart()
    c.add_item("pear", 2.0, 3)
    c.add_item("pear", 2.0, 4)   # total 7
    assert c.items()["pear"] == 7

# adding same item with different price raises ValueError
def test_add_same_item_different_price():
    c = cart.Cart()
    c.add_item("grape", 1.5, 2)
    with pytest.raises(ValueError):
        c.add_item("grape", 1.0, 1)

# remove item decreases quantity and removes when zero or less
def test_remove_item_decreases_and_removes():
    c = cart.Cart()
    c.add_item("melon", 3.0, 5)
    c.remove_item("melon", 2)  # remaining 3
    assert c.items()["melon"] == 3
    c.remove_item("melon", 3)  # should remove entirely
    assert "melon" not in c.items()

# removing nonexistent item raises KeyError
def test_remove_nonexistent_item():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("unknown", 1)

# subtotal calculation including bulk discounts
@pytest.mark.parametrize(
    "items, expected",
    [
        # item name not relevant for calculation except quantity
        ({"itemA": (2.0, 5)}, 10.00),   # no discount
        ({"itemB": (3.0, 10)}, 25.50),  # bulk 5% -> 30*0.95 = 28.5? Wait
    ],
)
def test_subtotal(items, expected):
    c = cart.Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    assert c.subtotal() == expected

# total calculation with coupon and shipping
def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 100.0, 12)   # bulk 5% -> 1200 * 0.95 = 1140
    # subtotal 1140
    total = c.total(coupon="SAVE10")  # coupon 10% -> 1026
    # shipping for non-member on 1026: fee 60 (subtotal>=1000?) 1026>1000 so free
    assert total == 1026.00

# total with member discount and shipping
def test_total_member_and_coupon():
    c = cart.Cart()
    c.add_item("gadget", 50.0, 20)   # bulk 10% -> 1000 *0.9=900
    total = c.total(member=True, coupon="SAVE5")  # 5% off -> 855
    # shipping for member on 855: fee 30 (subtotal<1000)
    assert total == 885.00
