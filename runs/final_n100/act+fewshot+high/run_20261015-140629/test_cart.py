import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.456, 20, round(123.456 * 0.8, 2)),
    ]
)
def test_apply_discount_basic(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [
        (-1, 10),
        (100, -5),
        (100, 105),
    ],
)
def test_apply_discount_invalid_values(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
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

@pytest.mark.parametrize(
    "quantity",
    [
        -1,
        0,
        3.5,
        "10",
    ],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  Save30 ", 30),
        ("sAvE40", 40),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",
        "SAVE51",
        "SAVEXX",
        "DISCOUNT10",
        "",
        "   ",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),
        (1000, False, 0),
        (5000, True, 0),
        (800, False, 60),
        (800, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [
        -1,
        -100.5,
    ],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}
    with pytest.raises(ValueError):
        c.add_item("apple", 0.90, 1)

def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -0.50, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.30, 0)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.30, -1)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.30, 2.5)

def test_cart_remove_and_total_quantity():
    c = cart.Cart()
    c.add_item("orange", 0.50, 4)
    assert c.items() == {"orange": 4}
    c.remove_item("orange", 3)
    assert c.items() == {"orange": 1}
    c.remove_item("orange", 5)
    assert "orange" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("grape", 1)

def test_cart_items_independence():
    c = cart.Cart()
    c.add_item("pear", 2.00, 1)
    items_copy = c.items()
    items_copy["pear"] = 100
    assert c.items() == {"pear": 1}

def test_cart_subtotal_empty_and_bulk():
    c = cart.Cart()
    assert c.subtotal() == 0.0

    c.add_item("apple", 1.00, 15)
    c.add_item("banana", 0.50, 60)
    expected_subtotal = round(14.25 + 27.0, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("widget", 10.00, 1)
    assert c.total() == round(10 + 60, 2)
    assert c.total(member=True) == round(10 + 30, 2)

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("gadget", 10.00, 1)
    assert c.total(coupon="SAVE10") == round(9.0 + 60, 2)
    assert c.total(member=True, coupon="SAVE10") == round(9.0 + 30, 2)

def test_cart_total_high_subtotal_free_shipping():
    c = cart.Cart()
    c.add_item("premium", 2000.00, 1)
    assert c.total(coupon="SAVE50") == round(1000 + 0, 2)

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("thing", 5.00, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
