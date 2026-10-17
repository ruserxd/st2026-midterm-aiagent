import pytest
import cart

# ---- utility helpers ----

def round2(x):
    return round(float(x), 2)

# ---- apply_discount tests ----
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == round2(expected)

@pytest.mark.parametrize("price, percent", [(-10, 20), (50, -5), (30, 105)])
def test_apply_discount_invalid_params(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent tests ----
@pytest.mark.parametrize("quantity, expected", [
    (0, None),  # will raise
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    if quantity <= 0:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(quantity)
    else:
        assert cart.bulk_discount_percent(quantity) == expected

# ---- parse_coupon tests ----
@pytest.mark.parametrize("code, percent", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", [
    "", "SAVEXX", "SAVE0", "SAVE51",
    "123", " SAVE -10 ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee tests ----
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# ---- Cart behavior tests ----
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_cart_totals(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0

# add_item and items

def test_add_and_items():
    c = cart.Cart()
    c.add_item("apple", unit_price=1, quantity=2)
    assert c.items() == {"apple": 2}
    # adding same name increases qty only if price matches
    c.add_item("apple", unit_price=1, quantity=3)
    assert c.items() == {"apple": 5}
    with pytest.raises(ValueError):
        c.add_item("apple", unit_price=2, quantity=1)

# remove_item and removal

def test_remove_item():
    c = cart.Cart()
    c.add_item("banana", unit_price=0.5, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items() == {"banana": 2}
    # remove remaining
    c.remove_item("banana", quantity=2)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("banana")

# subtotal calculation including bulk discounts

def test_subtotal_bulk_discount():
    c = cart.Cart()
    # 9 units: no discount
    c.add_item("widget", unit_price=10, quantity=9)
    assert round2(c.subtotal()) == 90.0
    # 10 units: 5% bulk discount
    c.remove_item("widget", quantity=9)  # remove all
    c.add_item("widget", unit_price=10, quantity=10)
    assert round2(c.subtotal()) == 95.0  # 100 - 5%
    # 50 units: 10% discount
    c.remove_item("widget", quantity=10)
    c.add_item("widget", unit_price=20, quantity=50)
    assert round2(c.subtotal()) == 900.0  # 1000 - 10%

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", unit_price=200, quantity=3)  # subtotal 600
    # no coupon, non-member: shipping 60 -> total 660
    assert round2(c.total(member=False)) == 660.0
    # member: shipping 30 -> 630
    assert round2(c.total(member=True)) == 630.0
    # with valid coupon SAVE10: 600 * .9 = 540, shipping 60 => 600
    assert round2(c.total(member=False, coupon="SAVE10")) == 600.0
    # invalid coupon raises
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
