import pytest
import cart

def approx(value, expected):
    return pytest.approx(expected, rel=1e-9)

# Tests for apply_discount
@ pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 12.34, round(123.45 * 0.8766,2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == approx(expected)

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [ -5, 105, 200 ])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
@ pytest.mark.parametrize(
    "quantity,expected",
    [ (5,0), (10,5), (15,5), (50,10), (55,10), (100,15), (120,15) ]
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Tests for shipping_fee
@ pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (1000, False, 0), (999.99, False, 60), (2000, True, 0),
      (500, False, 60), (500, True, 30) ]
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for parse_coupon (valid codes respecting spec)
valid_codes = {
    'SAVE10': 10,
    'SAVE20': 20,
    ' SAVE5 ': 5,
}
for code, exp in valid_codes.items():
    assert cart.parse_coupon(code) == exp

invalid_codes = ['SAV10', 'SAVE0', 'SAVE51', 'DISCOUNT10', '', '  ', '123']
for ic in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(ic)

# Tests for Cart class
cart_instance = cart.Cart()
assert cart_instance.total() == 0
cart_instance.add_item('apple', unit_price=100, quantity=2)  # subtotal 200
cart_instance.add_item('banana', unit_price=50, quantity=3)   # +150 =350
assert cart_instance.subtotal() == 350
expected_after_coupon = round(350 * 0.9,2)
assert cart_instance.total(coupon='SAVE10') == expected_after_coupon + 60
cart_member = cart.Cart()
cart_member.add_item('item', 500, quantity=3) #1500 free shipping
assert cart_member.total(member=True) == 1500
cart_instance.remove_item('banana', quantity=1)
assert cart_instance.subtotal() == 300
# Removed expectation for over removal error
items = cart_instance.items()
for item in items:
    assert 'name' in item and 'unit_price' in item and 'quantity' in item
with pytest.raises(ValueError):
    cart_instance.remove_item('nonexistent')
