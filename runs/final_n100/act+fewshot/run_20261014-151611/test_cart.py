import pytest
import cart

# ---- helper data ----

C1_NAME = "Widget"
C1_PRICE = 20.0
C2_NAME = "Gadget"
C2_PRICE = 35.5

# ----- basic functions -----

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.00),
    (100, 0, 100.00),
    (50, 100, 0.00)
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-10, 20), (10, -5), (10, 120)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount logic
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# coupon parsing
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("SaVe5", 5)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEX",   # non numeric
    "SAVExx",
    "SAVA10", # wrong prefix
    "save0",
    "save51",
    ""
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee logic
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (5000, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class tests -----

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.00
    assert c.total() == 0.00

# adding items

def test_add_item_basic():
    c = cart.Cart()
    c.add_item(C1_NAME, C1_PRICE)
    assert c.items() == {C1_NAME: 1}
    assert c.subtotal() == round(C1_PRICE * 1 * (100 - cart.bulk_discount_percent(1)) / 100, 2)


def test_add_multiple_quantities_and_same_item():
    c = cart.Cart()
    c.add_item(C1_NAME, C1_PRICE, quantity=5)
    assert c.items() == {C1_NAME: 5}
    # bulk discount applies to 5 units -> 0% (since <10)
    expected = round(C1_PRICE * 5 * 1.0, 2)
    assert c.subtotal() == expected
    # add same item again with same unit price
    c.add_item(C1_NAME, C1_PRICE, quantity=7)  # total 12 -> discount 5%
    assert c.items()[C1_NAME] == 12
    discount = cart.bulk_discount_percent(12)
    expected = round(C1_PRICE * 12 * (100 - discount) / 100, 2)
    assert c.subtotal() == expected

# adding item with different unit price raises ValueError

def test_add_item_different_price():
    c = cart.Cart()
    c.add_item(C1_NAME, C1_PRICE)
    with pytest.raises(ValueError):
        c.add_item(C1_NAME, C1_PRICE + 5.0)

# removing items

def test_remove_item_basic():
    c = cart.Cart()
    c.add_item(C2_NAME, C2_PRICE, quantity=3)
    c.remove_item(C2_NAME)  # removes one unit
    assert c.items()[C2_NAME] == 2
    # subtotal should reflect two units
    assert c.subtotal() == round(C2_PRICE * 2 * (100 - cart.bulk_discount_percent(2)) / 100, 2)


def test_remove_item_removes_when_zero():
    c = cart.Cart()
    c.add_item(C1_NAME, C1_PRICE, quantity=2)
    c.remove_item(C1_NAME, quantity=2)
    assert C1_NAME not in c.items()


def test_remove_nonexistent_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent")

# total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # add 10 Widgets -> bulk discount 5%
    c.add_item(C1_NAME, C1_PRICE, quantity=10)
    # subtotal after bulk: 20 * 10 * 0.95 = 190
    assert c.subtotal() == round(20.0 * 10 * 0.95, 2)
    # apply coupon SAVE10 -> 10% off of 190 => 171
    total_with_coupon = cart.apply_discount(c.subtotal(), cart.parse_coupon("SAVE10"))
    assert total_with_coupon == 171.00
    # shipping: subtotal after coupon is 171 (<1000), member False => fee 60
    shipping = cart.shipping_fee(total_with_coupon)
    assert shipping == 60
    expected_total = round(total_with_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total


def test_total_non_member_half_shipping():
    c = cart.Cart()
    c.add_item(C1_NAME, C1_PRICE, quantity=5)  # no bulk discount
    subtotal = round(20.0 * 5, 2)
    assert c.subtotal() == subtotal
    expected = round(subtotal + 60, 2)
    assert c.total(member=True) == expected

# invalid coupon on total raises ValueError

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item(C1_NAME, C1_PRICE)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
