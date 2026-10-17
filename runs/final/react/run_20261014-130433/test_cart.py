import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Helper for approximate equality

def approx(value):
    return round(float(value),2)

# Tests for apply_discount
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 10, 111.11),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert approx(apply_discount(price, percent)) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# Tests for bulk_discount_percent
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
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEX"] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1500, True, 0),
        (999.99, False, 60),
        (800, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Tests for Cart class

def test_cart_initial_empty():
    c = Cart()
    assert list(c.items()) == []
    assert c.subtotal() == 0
    assert c.total() == 0


def test_cart_add_and_subtotal():
    c = Cart()
    c.add_item("apple", unit_price=50, quantity=3)
    c.add_item("banana", unit_price=30)
    # subtotal: 3*50 + 1*30 = 180
    assert c.subtotal() == 180
    items = dict(c.items())
    assert items["apple"] == (50, 3)
    assert items["banana"] == (30, 1)


def test_cart_remove():
    c = Cart()
    c.add_item("item", unit_price=20, quantity=5)
    c.remove_item("item", quantity=2)
    assert dict(c.items())["item"] == (20, 3)
    # remove more than existing should set to zero and remove
    c.remove_item("item", quantity=5)
    assert "item" not in dict(c.items())


def test_cart_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("book", unit_price=200, quantity=1)
    # subtotal 200, coupon SAVE10 -> 180, shipping 60 (non-member) => 240
    assert approx(c.total(coupon="SAVE10")) == 240.0
    # member reduces shipping
    assert approx(c.total(member=True, coupon="SAVE10")) == 210.0


def test_cart_total_invalid_coupon():
    c = Cart()
    c.add_item("pen", unit_price=10)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Bulk discount integration: add many items and expect bulk percent applied by total? The spec does not apply bulk in total, only item-level. We test internal function.

if __name__ == "__main__":
    import pytest; pytest.main([__file__])
