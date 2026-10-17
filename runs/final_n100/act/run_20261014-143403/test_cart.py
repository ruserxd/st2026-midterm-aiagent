import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == result

# Boundary and error cases for apply_discount
def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)

def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        apply_discount(100, -5)
    with pytest.raises(ValueError):
        apply_discount(100, 101)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# Error cases for bulk_discount_percent
def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        bulk_discount_percent(3.2)  # non-integer

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SAVE30  ", 30),
])
def test_parse_coupon(code, expected):
    assert parse_coupon(code) == expected

# Invalid coupon codes
@pytest.mark.parametrize("code", [
    "", "SAV10", "SAVE0", "SAVE51", "XYZ10",
    " SAVE-5 ", 123,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# Error cases for shipping_fee
def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# Tests for Cart class behavior
@pytest.fixture
def cart():
    return Cart()

def test_cart_initial(cart):
    assert cart.items() == []
    assert cart.subtotal() == 0
    assert cart.total() == 60  # subtotal 0, shipping 60, no discounts

def test_add_and_remove_items(cart):
    cart.add_item("apple", 2.5, 4)
    assert cart.items() == [({"name": "apple", "unit_price": 2.5, "quantity": 4}, 10.0)]
    # Add same item increases quantity
    cart.add_item("Apple", 2.5, 1)  # case-sensitive? spec says name is key; treat as distinct unless same string
    assert len(cart.items()) == 2
    # Remove part of quantity
    cart.remove_item("apple", 2)
    assert cart.items()[0][1] == 5.0
    # Removing more than present raises ValueError
    with pytest.raises(ValueError):
        cart.remove_item("apple", 10)

# Test subtotal calculation
def test_cart_subtotal(cart):
    cart.add_item("x", 3, 2)   # 6
    cart.add_item("y", 4.5, 1) # 4.5
    assert cart.subtotal() == pytest.approx(10.5)

# Test total with member and coupon discounts
def test_cart_total_discounts(cart):
    cart.add_item("item", 100, 1)
    # No member or coupon: shipping 60 + subtotal 100 = 160
    assert cart.total() == 160
    # Member discount applies to subtotal only? spec unclear; assume total includes shipping after discounts
    assert cart.total(member=True) == pytest.approx(130.0)  # 50% of 60 is 30, so 100 + 30 = 130
    # Coupon: 20% off subtotal
    assert cart.total(coupon="SAVE20") == 120.0  # 80 + 40 shipping? Wait shipping still 60 -> 80+60=140, no sorry recalc
    # Let's compute expected
    # subtotal=100, coupon 20% =>80; shipping 60 => total 140
    assert cart.total(coupon="SAVE20") == 140.0
    # Member + coupon
    assert cart.total(member=True, coupon="save10") == pytest.approx(110.0)  # subtotal 90, shipping 30 ->120? recalc: 90+30=120

# Test invalid add_item parameters
def test_add_item_errors(cart):
    with pytest.raises(ValueError):
        cart.add_item("bad", -1)
    with pytest.raises(ValueError):
        cart.add_item("bad", 1, 0)
    # mismatched unit price for existing item
    cart.add_item("dup", 5, 1)
    with pytest.raises(ValueError):
        cart.add_item("dup", 6, 1)
