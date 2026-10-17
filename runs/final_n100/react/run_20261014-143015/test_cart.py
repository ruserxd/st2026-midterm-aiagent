import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# Shipping fee tests (unchanged)
@pytest.mark.parametrize("subtotal,expected", [
    (0, 60),          # minimum subtotal still requires shipping
    (999.99, 60),     # just below free threshold
    (1000, 0),        # exactly threshold
    (1500, 0),        # above threshold
])
def test_shipping_fee(subtotal, expected):
    assert shipping_fee(subtotal) == expected

# Non‑member half fee check
@pytest.mark.parametrize("subtotal,expected", [
    (200, 30),   # member discount halves the fee
    (0, 30),     # even if no items, a member pays half shipping
])
def test_shipping_fee_member(subtotal, expected):
    assert shipping_fee(subtotal, member=True) == expected

# Invalid subtotal should raise ValueError
@pytest.mark.parametrize("subtotal", [ -1, -100.5 ])
def test_shipping_fee_invalid_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Apply discount tests (unchanged)
@pytest.mark.parametrize(
    "price,percent,expected", [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),    # no discount
        (50, 100, 0.0),     # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == expected

# Value checks for price and percent
@pytest.mark.parametrize("price", [ -1, -10.5 ])
def test_apply_discount_invalid_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-10, 110])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# Bulk discount percent tests (aligned to spec)
@pytest.mark.parametrize(
    "quantity,expected", [
        (0, 0),
        (5, 0),
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

# Invalid quantity raises ValueError
@pytest.mark.parametrize("quantity", [ -1, -5, 0.5, '10'])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# Coupon parsing tests (aligned to spec)
@pytest.mark.parametrize(
    "code,expected", [
        ('SAVE10', 10),
        ('save50', 50),
        (' SAVE20 ', 20),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# Invalid coupon raises ValueError
@pytest.mark.parametrize("code", [ None, '', 'INVALID', 'SAVE0', 'SAVE51', '100', '1234'] )
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Cart class tests (simplified)

def test_cart_add_and_subtotal():
    cart = Cart()
    cart.add_item('apple', 2.5)
    cart.add_item('banana', 1.0, quantity=3)
    assert cart.subtotal() == pytest.approx(2.5 + 3 * 1.0)


def test_cart_remove_and_items():
    cart = Cart()
    cart.add_item('orange', 4, quantity=5)
    cart.remove_item('orange')  # remove one unit
    assert len(cart.items()) == 1
    name, (unit_price, qty) = next(iter(cart.items()))
    assert name == 'orange'
    assert unit_price == 4
    assert qty == 4


def test_cart_total_with_member_and_coupon():
    cart = Cart()
    cart.add_item('book', 1200)
    total = cart.total(member=True, coupon='SAVE10')
    expected_subtotal = 1200
    discounted = apply_discount(expected_subtotal, 10)
    assert total == pytest.approx(discounted)


def test_cart_total_without_member_and_no_coupon():
    cart = Cart()
    cart.add_item('pen', 5)
    subtotal = 5
    shipping = shipping_fee(subtotal)
    expected_total = round(subtotal + shipping, 2)
    assert cart.total() == expected_total

# Member half‑shipping when applicable

def test_cart_total_member_half_shipping():
    cart = Cart()
    cart.add_item('mug', 30)
    subtotal = 30
    # member pays half shipping: 30 + (60/2) = 60
    assert cart.total(member=True) == pytest.approx(60.0)

# Removing nonexistent item raises KeyError

def test_cart_remove_nonexistent_item_raises():
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item('nonexistent')
