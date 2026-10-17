import pytest
import cart

# Helper: create a cart with one item

def make_simple_cart():
    c = cart.Cart()
    c.add_item("apple", unit_price=100, quantity=1)
    return c

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),
        (50, 0, 50.0),
        (80.25, 10, 72.23),  # rounded
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (200, 110)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@ pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.3],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@ pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25 ", 25),
        ("  SaVe1  ", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@ pytest.mark.parametrize(
    "code",
    ["SAVE0", "save51", "SAVEx", "ABC10", " ", ""] ,
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@ pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (500, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
        (200, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize(
    "subtotal",
    [-10, -1.5],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart item management

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("book", unit_price=1200, quantity=2)
    assert c.items() == [{"name": "book", "unit_price": 1200, "quantity": 2}]
    c.remove_item("book", quantity=1)
    assert c.items() == [{"name": "book", "unit_price": 1200, "quantity": 1}]
    # removing more than present should raise
    with pytest.raises(ValueError):
        c.remove_item("book", quantity=5)

# subtotal calculation

def test_subtotal():
    c = cart.Cart()
    c.add_item("pen", unit_price=50, quantity=3)  # 150
    c.add_item("notebook", unit_price=200, quantity=1)  # 200
    assert c.subtotal() == 350

# total with coupon and shipping

def test_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", unit_price=2000, quantity=1)
    # subtotal 2000 => free shipping
    assert c.total(member=True) == 2000.00

@ pytest.mark.parametrize(
    "items, coupon_code, member, expected",
    [
        (
            [("apple", 100, 5)],  # subtotal 500
            None,
            False,
            560.0,  # 500 + 60 shipping
        ),
        (
            [("apple", 100, 5)],  # 500
            "SAVE10",
            False,
            500 * 0.9 + 60,  # discount before shipping
        ),
        (
            [("big", 900, 1)],  # subtotal 900
            None,
            True,
            900 + 30,  # member half shipping
        ),
    ],
)
def test_total_various(items, coupon_code, member, expected):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, unit_price=price, quantity=qty)
    total = c.total(member=member, coupon=coupon_code)
    assert round(total, 2) == round(expected, 2)

# total with empty cart

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.00

# total with invalid coupon should raise

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("x", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
