import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent, apply_discount

# Coupon parsing tests

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe5") == 5

@pytest.mark.parametrize('code', ["DISCOUNT", "save0", "SAVE51", "SAVE-5", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError, match="invalid coupon"):
        parse_coupon(code)

# Shipping fee tests

def test_shipping_fee():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        shipping_fee(-1)

# Bulk discount percent tests

def test_bulk_discount_percent_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(250) == 15

@pytest.mark.parametrize('q', [0, -3, 2.5])
def test_bulk_discount_percent_invalid(q):
    with pytest.raises(ValueError):
        bulk_discount_percent(q)

# Apply discount tests

def test_apply_discount_basic():
    assert apply_discount(100, 10) == 90

# Cart tests

def test_cart_subtotal_and_items():
    c = Cart()
    assert c.subtotal() == 0
    c.add_item("apple", unit_price=1.00, quantity=3)
    c.add_item("banana", unit_price=2.50)
    assert c.items()["apple"] == {"unit_price": 1.00, "quantity": 3}
    assert c.items()["banana"] == {"unit_price": 2.50, "quantity": 1}
    assert c.subtotal() == 3*1 + 2.5

def test_cart_remove_and_error():
    c = Cart()
    c.add_item("orange", unit_price=0.5, quantity=4)
    c.remove_item("orange", quantity=2)
    assert c.items()["orange"]["quantity"] == 2
    with pytest.raises(ValueError):
        c.remove_item("orange", quantity=3)

def test_cart_total_no_coupon_member():
    c = Cart()
    c.add_item("item1", unit_price=200, quantity=2)  # subtotal 400
    assert round(c.total(), 2) == 460

def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("premium", unit_price=500, quantity=1)
    assert round(c.total(member=True, coupon="SAVE20"), 2) == 430

def test_cart_total_invalid_coupon_raises():
    c = Cart(); c.add_item("x", unit_price=10)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_empty_cart_total_zero_and_no_shipping():
    c = Cart()
    assert c.total() == 0
