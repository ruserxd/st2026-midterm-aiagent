import pytest
import cart

# ---- Helper function tests based on specification ----

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent according to spec
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),  # spec says >=50 ->10
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon case-insensitive and whitespace tolerant
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE50 ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOPE", "save-5", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests per spec
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class tests based on specification ----

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 2.5, quantity=3)
    c.add_item("banana", 1.2)
    items = c.items()
    assert len(items) == 2
    assert items["apple"] == 3
    assert items["banana"] == 1
    # subtotal check using spec: apply bulk discount on quantities
    expected_subtotal = round(2.5 * 3 + 1.2, 2)  # 7.5 +1.2=8.7
    assert c.subtotal() == expected_subtotal
    # remove some apples
    c.remove_item("apple", quantity=2)
    items = c.items()
    assert items["apple"] == 1
    # removing all should delete the entry
    c.remove_item("apple")
    items = c.items()
    assert "apple" not in items and items["banana"] == 1


def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# total without coupon or member per spec

def test_total_no_coupon_or_member():
    c = cart.Cart()
    c.add_item("item", 100, quantity=2)  # subtotal 200
    # After coupon none: amount=200, shipping fee for non-member on 200 ->60
    expected_total = round(200 + cart.shipping_fee(200, False), 2)
    assert c.total() == expected_total

# total with member discount and coupon per spec

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("expensive", 500, quantity=1)  # subtotal 500
    # Apply coupon SAVE10 -> 10% off =>450
    # shipping after coupon for non-member:60 ->510
    assert c.total(member=False, coupon="SAVE10") == pytest.approx(510.0)
    # member half shipping 30 ->480
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(480.0)

# total with invalid coupon raises ValueError per spec

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 100)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# empty cart returns 0 and no shipping

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# rounding to two decimals

def test_total_rounding():
    c = cart.Cart()
    # subtotal not integral to cause rounding
    c.add_item("round", 1.005, quantity=100)  # 100.5
    # no coupon; shipping 60 ->160.5 rounded to 160.50
    assert c.total() == pytest.approx(160.5)
