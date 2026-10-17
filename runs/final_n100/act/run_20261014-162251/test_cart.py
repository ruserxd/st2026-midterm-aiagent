import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper data ----------
@pytest.fixture
def simple_cart():
    c = Cart()
    c.add_item("Apple", 100, 5)   # subtotal 500
    c.add_item("Banana", 50, 10)  # subtotal 500
    return c

# ---------- Tests for apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 101, 200],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.5])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEXX", "   "]) 
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- Tests for shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart class ----------
def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # free subtotal + shipping

def test_add_and_remove_items(simple_cart):
    c = simple_cart
    assert c.items()["Apple"] == (100, 5)
    assert c.items()["Banana"] == (50, 10)
    assert c.subtotal() == 1000
    # remove some bananas
    c.remove_item("Banana", 4)
    assert c.items()["Banana"] == (50, 6)
    assert c.subtotal() == 800
    # remove all apples
    c.remove_item("Apple", 5)
    assert "Apple" not in c.items()

def test_cart_total_with_coupon_and_member(simple_cart):
    c = simple_cart
    # subtotal 1000, shipping 0
    total_no_discount = c.total(member=True)
    assert total_no_discount == 1000
    # apply coupon SAVE10 => 10% off on subtotal (before shipping)
    total_coupon = c.total(member=False, coupon="SAVE10")
    expected_after_coupon = apply_discount(1000, 10)  # 900.0
    assert total_coupon == expected_after_coupon
    # with member shipping is free anyway
    total_member_and_coupon = c.total(member=True, coupon="save20")
    assert total_member_and_coupon == apply_discount(1000, 20)

# ---------- Edge cases for Cart removal and quantity ---------
def test_remove_more_than_exists(simple_cart):
    c = simple_cart
    with pytest.raises(ValueError):
        c.remove_item("Apple", 10)  # only 5 available

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__]))
