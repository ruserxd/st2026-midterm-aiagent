import pytest
import cart

# ---------- Helper data ----------

# sample items for testing
ITEMS = [
    ("apple", 10.0, 5),   # bulk discount 5%
    ("banana", 20.0, 12), # bulk discount 5%
    ("cherry", 50.0, 55), # bulk discount 10%
    ("durian", 100.0, 120) # bulk discount 15%
]

# ---------- Function tests ----------

@ pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50.5, 20, 40.4)
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@ pytest.mark.parametrize("price, percent", [(-10, 50), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@ pytest.mark.parametrize("qty, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@ pytest.mark.parametrize("qty", [0, -1, 3.5, "10"])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SaVe30 ", 30),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "ABC10", "SAVExx"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@ pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (1200, True, 0),
    (999.99, False, 60),
    (999.99, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_item_basic():
    c = cart.Cart()
    c.add_item("book", 30, 2)
    assert c.items() == {"book": 2}
    assert c.subtotal() == pytest.approx(60.0)
    # remove part
    c.remove_item("book", 1)
    assert c.items() == {"book": 1}
    assert c.subtotal() == pytest.approx(30.0)
    # remove all
    c.remove_item("book")
    assert c.items() == {}

def test_add_same_item_with_different_price_raises():
    c = cart.Cart()
    c.add_item("pen", 5, 3)
    with pytest.raises(ValueError):
        c.add_item("pen", 6, 1)

# bulk discount effect in subtotal
def test_subtotal_bulk_discounts():
    c = cart.Cart()
    for name, price, qty in ITEMS:
        c.add_item(name, price, qty)
    # compute expected subtotal manually
    expected = 0.0
    for name, price, qty in ITEMS:
        discount = cart.bulk_discount_percent(qty)
        amount = price * qty * (1 - discount / 100)
        expected += amount
    assert c.subtotal() == pytest.approx(round(expected,2))

# total with coupon and shipping
def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200.0, 5)  # qty=5 -> bulk 5% => 190 per unit
    # subtotal: 190*5=950
    assert c.subtotal() == pytest.approx(950.0)
    total_no_coupon = c.total()
    # subtotal 950 < 1000, non-member => +60 shipping => 1010
    assert total_no_coupon == pytest.approx(1010.0)
    # with coupon 10%
    total_with_coup = c.total(coupon="SAVE10")
    # after discount: 950*0.9=855, shipping 60 => 915
    assert total_with_coup == pytest.approx(915.0)
    # member and invalid coupon should raise ValueError when parsing
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# total of empty cart is zero no shipping
def test_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0

# remove_item raises KeyError for unknown item
def test_remove_nonexistent_item_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("ghost")

# invalid add_item parameters
@pytest.mark.parametrize("name, unit_price, qty", [
    ("foo", -1, 1),
    ("bar", 5, 0),
    ("baz", 10, -2),
    ("qux", "20", 1)
])
def test_add_item_invalid(name, unit_price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, qty)

# bulk discount percent for non-integer quantity in Cart should be caught by add_item
@pytest.mark.parametrize("qty", [10.5, "15"])
def test_add_item_nonint_qty(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("test", 1.0, qty)
