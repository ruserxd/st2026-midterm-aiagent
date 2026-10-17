import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Helper for rounding in tests
def round2(val):
    return round(float(val), 2)

######################
# Tests for apply_discount
######################

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

# Edge values
@pytest.mark.parametrize("price,percent", [
    (0, 50),
    (123.45, 25)
])
def test_apply_discount_varied(price, percent):
    expected = price * (1 - percent / 100)
    assert round2(apply_discount(price, percent)) == round2(expected)

# Invalid inputs
@pytest.mark.parametrize("price", [-0.01, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-1, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

######################
# Tests for bulk_discount_percent
######################

def test_bulk_discount_percent_basic():
    # Assuming simple linear discount: 0% until 10, 5% at 10-19, etc.
    assert bulk_discount_percent(1) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(20) == 10

######################
# Tests for parse_coupon
######################

def test_parse_coupon_valid():
    # Valid format: two-letter code followed by hyphen and digits, e.g., 'AB-123'
    code = "XY-99"
    assert parse_coupon(code) == 0.99

@pytest.mark.parametrize("code", ["A1-23", "ABC-12", "ab-45", "AB123", "AB-1"])
def test_parse_coupon_invalid_format(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

######################
# Tests for shipping_fee
######################

def test_shipping_fee_basic():
    assert shipping_fee(0) == 5.0
    assert shipping_fee(100, member=True) == 0.0
    assert shipping_fee(120, member=False) == 7.5

######################
# Tests for Cart class
######################

@pytest.fixture
def cart():
    return Cart()

def test_cart_initial(cart):
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == pytest.approx(5.0)

def test_add_item(cart):
    cart.add_item("apple", 1.00, quantity=3)
    assert cart.items()["apple"] == [1.00, 3]
    assert cart.subtotal() == 3.0

def test_remove_item(cart):
    cart.add_item("banana", 2.50, quantity=4)
    cart.remove_item("banana", quantity=2)
    assert cart.items()["banana"] == [2.5, 2]
    # Removing more than present should raise error
    with pytest.raises(ValueError):
        cart.remove_item("banana", quantity=3)

def test_total_with_member_and_coupon(cart):
    cart.add_item("item1", 50, quantity=2)  # subtotal 100
    coupon_code = "CD-20"
    assert parse_coupon(coupon_code) == 0.20
    total = cart.total(member=True, coupon=coupon_code)
    # member gets free shipping; no discount applied because percentage is 0.2
    assert round(total, 2) == pytest.approx(100.0)

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-q", __file__]))
