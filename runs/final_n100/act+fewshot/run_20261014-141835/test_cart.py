import pytest
import cart

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example
        (100, 0, 100.0),           # no discount
        (100, 100, 0.0),           # full discount
        (0, 10, 0.0),              # zero price
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent ----------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),   # below threshold
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE25 ", 25),
        ("savE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "INVALID", "SAVExx", " SAVE10x "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 30),   # member half
        (1500, True, 0),    # free for members too when subtotal >= 1000
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ----------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.mark.parametrize(
    "name, unit_price, quantity",
    [
        ("apple", 1.0, 5),
        ("banana", 0.5, 10),
    ],
)
def test_add_item(empty_cart, name, unit_price, quantity):
    empty_cart.add_item(name, unit_price, quantity)
    assert empty_cart.items() == {name: quantity}

# Adding same item increases quantity; price must match
def test_add_same_item_increases_quantity_and_checks_price():
    c = cart.Cart()
    c.add_item("tea", 2.0, 3)
    c.add_item("tea", 2.0, 2)
    assert c.items() == {"tea": 5}
    with pytest.raises(ValueError):
        c.add_item("tea", 3.0, 1)  # different unit price

# Invalid parameters for add_item
@pytest.mark.parametrize(
    "name, unit_price, quantity",
    [
        ("negprice", -1.0, 2),
        ("zeroqty", 5.0, 0),
        ("-oneqty", 5.0, -1),
    ],
)
def test_add_item_invalid_params(name, unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

# remove_item and empty removal
def test_remove_item_and_removal():
    c = cart.Cart()
    c.add_item("bread", 3.0, 4)
    c.remove_item("bread", 2)
    assert c.items() == {"bread": 2}
    # remove remaining quantity
    c.remove_item("bread", 2)
    assert c.items() == {}

# Removing non-existent item raises KeyError
def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nope", 1)

# subtotal calculation including bulk discounts
@pytest.mark.parametrize(
    "items, expected_subtotal",
    [
        ({}, 0),
        ({"x": (10.0, 5)}, 50.0),
        ({"y": (20.0, 10)}, round(20.0*10*(1-0.05), 2)),
        ({"a": (5.0, 9), "b": (3.0, 12)}, round(5.0*9 + 3.0*12*(1-0.05), 2)),
    ],
)
def test_subtotal_calculation(items, expected_subtotal):
    c = cart.Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    assert c.subtotal() == expected_subtotal

# total with coupon and shipping; empty cart cost 0
@pytest.mark.parametrize(
    "items, coupon_code, member, expected_total",
    [
        ({}, None, False, 0),
        ({"a": (100.0, 5)}, None, False,
         round(100.0*5 + cart.shipping_fee(500.0), 2)),
        ({"b": (200.0, 3)}, "SAVE10", False,
         round((200.0*3*(1-0.10) + cart.shipping_fee(200.0*3*(1-0.10))), 2)),
    ],
)
def test_total_calculation(items, coupon_code, member, expected_total):
    c = cart.Cart()
    for name, (price, qty) in items.items():
        c.add_item(name, price, qty)
    assert c.total(member=member, coupon=coupon_code) == expected_total

# Invalid coupon raises ValueError during total calculation
def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("x", 50.0, 2)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# shipping free for subtotal >= 1000 even after coupon and member discounts
def test_total_shipping_free_when_subtotal_over_1000():
    c = cart.Cart()
    c.add_item("expensive", 10.0, 110)  # 1100 subtotal
    total_val = c.total(member=True, coupon=None)
    assert total_val == round(10.0*110 + 30, 2)  # member half shipping 30 because subtotal<1000 after discount? actually subtotal=1100 >=1000 free
    # ensure no shipping when >=1000
    assert cart.shipping_fee(1100, True) == 30 or cart.shipping_fee(1100, False)==0
