import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SaVe30 ", 30),
        ("SAVE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAV10",      # missing 'E'
        "SAVE0",      # percent < 1
        "SAVE101",    # percent > 50
        "SAVE-5",     # negative number
        "SAVE 10",    # space between prefix and number
        "SAVE+10",    # plus sign
        "SAVEabc",    # non-numeric suffix
        "",           # empty string
        "   ",       # only whitespace
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize(
    "price,percent",
    [
        (-10, 20),   # negative price
        (50, -5),    # negative percent
        (30, 110),   # percent > 100
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
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
def test_bulk_discount_percent_valid(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (50, True, 30),
    ],
)
def test_shipping_fee_valid(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------
@pytest.fixture
def empty_cart():
    return Cart()

def test_empty_cart_total(empty_cart):
    assert empty_cart.total() == 0.0

def test_add_and_subtotal(empty_cart):
    empty_cart.add_item("apple", 2.5, quantity=4)
    assert empty_cart.subtotal() == pytest.approx(10.0)
    # Adding same item increases quantity
    empty_cart.add_item("apple", 2.5, quantity=1)
    assert empty_cart.items()["apple"]["quantity"] == 5
    assert empty_cart.subtotal() == pytest.approx(12.5)

def test_remove_item(empty_cart):
    empty_cart.add_item("banana", 1.0, quantity=3)
    empty_cart.remove_item("banana", quantity=2)
    assert empty_cart.items()["banana"]["quantity"] == 1
    # Removing more than available removes item entirely
    empty_cart.remove_item("banana", quantity=5)
    assert "banana" not in empty_cart.items()

def test_total_with_coupon_and_shipping(empty_cart):
    empty_cart.add_item("widget", 50.0, quantity=2)  # subtotal 100
    total = empty_cart.total(coupon="SAVE10")  # 10% off -> 90; shipping 60 (not member)
    assert total == pytest.approx(150.0)

def test_total_member_discount_and_free_shipping(empty_cart):
    empty_cart.add_item("expensive", 500.0, quantity=3)  # subtotal 1500 >1000 free shipping
    total = empty_cart.total(member=True, coupon="SAVE20")  # 20% off -> 1200; free shipping
    assert total == pytest.approx(1200.0)

# Edge case: invalid coupon passed to total

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("item", 10)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="INVALID")
