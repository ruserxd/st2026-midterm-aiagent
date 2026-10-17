import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (100, 50, 50.0),
        (123.45, 0, 123.45),
        (0, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize("percent", [ -5, 105])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---- bulk_discount_percent ----------------------------------------------
@ pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---- parse_coupon -------------------------------------------------------
@ pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save50", 50),
        ("   SaVe1  ", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVe0",          # below 1
        "SAVE51",         # above 50
        "DISCOUNT10",     # wrong prefix
        "" ,              # empty
        " SAVE-5 ",       # negative
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---- shipping_fee -------------------------------------------------------
@ pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1500.5, True, 0),
        (999.99, False, 60),
        (500, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---- Cart -----------------------------------------------------------------

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

@ pytest.mark.parametrize(
    "name,unit_price,quantity",
    [
        ("apple", 1.0, 5),
        ("banana", 2.5, 3),
    ],
)
def test_cart_add_and_subtotal(name, unit_price, quantity):
    c = Cart()
    c.add_item(name, unit_price, quantity)
    assert c.items() == {name: quantity}
    expected = unit_price * quantity
    # no bulk discount for quantity<10
    assert c.subtotal() == pytest.approx(round(expected, 2))

@ pytest.mark.parametrize("quantity", [0, -1])
def test_cart_add_invalid(quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("apple", 1.0, quantity)

def test_cart_duplicate_add_different_price():
    c = Cart()
    c.add_item("apple", 1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5, 3)

# bulk discount scenario
@ pytest.mark.parametrize(
    "quantity,expected_discount",
    [
        (10, 5),
        (50, 10),
        (100, 15),
    ],
)
def test_cart_bulk_discount(quantity, expected_discount):
    c = Cart()
    unit_price = 10.0
    c.add_item("widget", unit_price, quantity)
    # subtotal before discount
    raw_total = unit_price * quantity
    # apply bulk discount percent
    discounted = apply_discount(raw_total, expected_discount)
    assert c.subtotal() == pytest.approx(round(discounted, 2))

@ pytest.mark.parametrize(
    "name,quantity_removed",
    [
        ("apple", 1),
    ],
)
def test_cart_remove_item(name, quantity_removed):
    c = Cart()
    c.add_item(name, 5.0, 3)
    c.remove_item(name, quantity_removed)
    assert c.items() == {name: 2}

@ pytest.mark.parametrize("quantity_removed", [4])
def test_cart_remove_last_items(quantity_removed):
    c = Cart()
    c.add_item("orange", 2.0, 3)
    c.remove_item("orange", quantity_removed)
    assert c.items() == {}

@ pytest.mark.parametrize("missing_item", ["pear"])
def test_cart_remove_nonexistent(missing_item):
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item(missing_item, 1)

# total calculation with coupon and shipping
def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    # subtotal $200 -> no bulk discount (quantity 5)
    c.add_item("book", 40.0, 5)
    assert c.subtotal() == 200.0
    # apply coupon 10%
    total_before_shipping = apply_discount(200.0, 10)
    shipping = shipping_fee(total_before_shipping, member=False)
    expected_total = round(total_before_shipping + shipping, 2)
    assert c.total(coupon="SAVE10") == pytest.approx(expected_total)

# no shipping on empty cart
def test_cart_total_empty_no_shipping():
    c = Cart()
    assert c.total() == 0.0

# member discount for shipping
def test_cart_member_shipping_fee():
    c = Cart()
    c.add_item("item", 1.0, 10)  # bulk discount 5%
    subtotal = c.subtotal()
    # total before shipping includes coupon if any
    total_before_shipping = apply_discount(subtotal, 0)
    shipping = shipping_fee(total_before_shipping, member=True)
    expected_total = round(total_before_shipping + shipping, 2)
    assert c.total(member=True) == pytest.approx(expected_total)

# invalid coupon in Cart.total
def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("item", 5.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
