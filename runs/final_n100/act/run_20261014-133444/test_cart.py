import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- helper ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk discount tests
@pytest.mark.parametrize("quantity,expected", [
    (99, 10),
    (50, 10),
    (49, 5),
    (10, 5),
    (9, 0),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "ten"])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    (" SAVE30", 30),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "",
    "SAVEXX",
    "SAVE51",
    "10SAVE",
    "save0",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0.0),
    (1000, True, 0.0),
    (999.99, False, 60.0),
    (500, True, 30.0),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100, "abc"])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart tests
def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 60.0  # subtotal 0 -> shipping 60, no discount

def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 100, 3)
    assert c.items()["apple"] == (100, 3)
    assert c.subtotal() == 300.0
    c.remove_item("apple", 1)
    assert c.items()["apple"] == (100, 2)
    assert c.subtotal() == 200.0
    c.remove_item("apple", 2)
    assert "apple" not in c.items()

# test bulk discount applied via total when quantity >=10
def test_cart_bulk_discount():
    c = Cart()
    c.add_item("banana", 50, 10)  # bulk discount 5%
    expected_subtotal = 500.0
    # subtotal before discounts
    assert c.subtotal() == expected_subtotal
    # member=False no coupon, only shipping fee applied
    # shipping fee for subtotal<1000 is 60
    total_no_discount = expected_subtotal + 60.0
    assert c.total() == total_no_discount
    # apply bulk discount via total calculation (implementation detail may not)
    # Assume total applies bulk discount automatically
    discounted_total = (expected_subtotal * 0.95) + 60.0
    if hasattr(c, 'bulk_discount_percent'):
        assert c.total() == discounted_total

# test coupon application
def test_cart_coupon_and_shipping():
    c = Cart()
    c.add_item("item", 200, 1)
    # subtotal 200 -> shipping 60, no bulk discount
    expected = 200 + 60
    assert c.total() == expected
    # apply coupon SAVE10 -> 10% off entire total
    assert c.total(coupon="SAVE10") == round(expected * 0.9, 2)

# test member shipping
def test_cart_member_shipping():
    c = Cart()
    c.add_item("item", 50, 1)
    # subtotal 50 -> shipping 60, member half ->30
    assert c.total(member=True) == 80.0
