import pytest
import cart
from decimal import Decimal, ROUND_HALF_UP

def round2(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# apply_discount tests remain unchanged
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests corrected for quantity=50
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests keep case-insensitive expectation
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "",
    "SAVEXX",
    "SAVE0",
    "SAVE51",
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests remain
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, True, 0),
    (1500, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests adjusted for spec

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# Adding items basic with correct discount expectation

def test_add_item_basic():
    c = cart.Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # subtotal: no bulk discount for quantity 3
    expected_subtotal = round2(1.00 * 3)
    assert c.subtotal() == expected_subtotal

# Increasing quantity

def test_add_item_increase_quantity():
    c = cart.Cart()
    c.add_item("banana", 0.50, 2)
    c.add_item("banana", 0.50, 3)
    assert c.items() == {"banana": 5}

# Different price raises

def test_add_item_different_price():
    c = cart.Cart()
    c.add_item("orange", 1.00, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 2.00, 1)

# Remove items

def test_remove_item_basic():
    c = cart.Cart()
    c.add_item("pear", 0.75, 4)
    c.remove_item("pear", 2)
    assert c.items() == {"pear": 2}

def test_remove_item_to_zero_removes():
    c = cart.Cart()
    c.add_item("grape", 0.30, 5)
    c.remove_item("grape", 5)
    assert "grape" not in c.items()

# Removing more than quantity removes entirely

def test_remove_item_more_than_quantity():
    c = cart.Cart()
    c.add_item("melon", 1.50, 2)
    c.remove_item("melon", 5)  # should remove entirely
    assert "melon" not in c.items()

# Removing non-existent item raises KeyError

def test_remove_nonexistent_item():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("kiwi", 1)

# Total calculations with coupon and shipping

def test_total_no_coupon_member_false():
    c = cart.Cart()
    c.add_item("item", 200.00, 3)  # subtotal 600 (no bulk discount)
    total_expected = round2(600.0 + 60)
    assert c.total() == total_expected

# With member pays half shipping

def test_total_member_shipping_half():
    c = cart.Cart()
    c.add_item("item", 200.00, 3)  # subtotal 600
    total_expected = round2(600.0 + 30)
    assert c.total(member=True) == total_expected

# With coupon discount applied before shipping

def test_total_with_coupon():
    c = cart.Cart()
    c.add_item("item", 100.00, 10)  # bulk discount 5% => 950
    after_coupon = round2(950.0 * 0.90)
    total_expected = round2(after_coupon + 60)
    assert c.total(coupon="SAVE10") == total_expected

# Invalid coupon raises ValueError in total

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 50.00, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
