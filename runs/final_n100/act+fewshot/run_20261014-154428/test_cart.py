import pytest
import cart

# Helper to round to 2 decimals consistently
def r(x):
    return round(float(x), 2)

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == r(result)

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Bulk discount tests
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (51, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -3, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Coupon parsing tests
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    "  SaVe30 ": 30,
}
@pytest.mark.parametrize("code,expected", valid_codes.items())
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["DISCOUNT10", "SAVE0", "SAVE51", "SAVEXX", 123]
for code in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee tests
assertions = [ (0, False, 60), (999.99, True, 30), (1000, False, 0) ]
@pytest.mark.parametrize("subtotal,member,fee", assertions)
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == r(fee)

with pytest.raises(ValueError):
    cart.shipping_fee(-5)

# Cart tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_cart_totals(empty_cart):
    assert empty_cart.subtotal() == 0.00
    assert empty_cart.total() == 0.00

def test_add_and_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 1, 5)
    c.add_item("banana", 2, 3)
    assert c.items() == {"apple":5, "banana":3}

# Bulk discount on cart subtotal
def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    # 10 apples at $1 -> bulk 5% off
    c.add_item("apple", 1, 10)
    expected = r(1*10*(100-5)/100)  # 9.5
    assert c.subtotal() == expected

# Coupon application and shipping
def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, 2)  # $400 total, no bulk discount (qty=2)
    subtotal = r(400)
    # apply coupon SAVE10 -> 40 off => 360
    amount_after_coupon = r(subtotal * 0.90)
    shipping = cart.shipping_fee(subtotal, member=False)
    expected_total = r(amount_after_coupon + shipping)
    assert c.total(coupon="SAVE10") == expected_total

# Removing items
def test_remove_item_and_zero_removal():
    c = cart.Cart()
    c.add_item("thing", 5, 3)
    c.remove_item("thing", 1)
    assert c.items() == {"thing":2}
    c.remove_item("thing", 2)  # should remove entirely
    assert "thing" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("unknown")
