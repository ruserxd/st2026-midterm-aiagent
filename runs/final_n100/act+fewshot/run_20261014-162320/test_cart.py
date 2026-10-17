import pytest
import cart

# Test apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Test apply_discount errors
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Test bulk_discount_percent
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
    assert cart.bulk_discount_percent(quantity) == expected

# Errors in bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -5, 1.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Test parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupons
@pytest.mark.parametrize("code", ["SAVE0", "SAVEXX", "foo", "", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal,expected", [
    (999, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# Shipping fee for members
@pytest.mark.parametrize("subtotal,expected", [
    (999, 30),
    (1000, 0),
])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

# Shipping fee errors
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Test Cart class
def test_cart_basic_operations():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0.0
    c.add_item("apple", 1.5, quantity=2)
    assert c.items() == [("apple", 1.5, 2)]
    assert c.subtotal() == 3.0
    c.remove_item("apple", quantity=1)
    assert c.items() == [("apple", 1.5, 1)]
    assert c.subtotal() == 1.5
    c.remove_item("apple", quantity=1)
    assert c.items() == []
    assert c.subtotal() == 0.0

# Test total calculation with discounts and shipping
@pytest.mark.parametrize(
    "items,member,coupon,total_expected",
    [
        # No discount, non-member, no coupon
        ([("item", 10), ("item2", 20)], False, None, 30.0 + 60),
        # Bulk discount on quantity >=10
        ([("item", 10)] * 12, False, None, cart.apply_discount(120, 5) + 60),
        # Coupon discount applied after shipping? Assume after subtotal.
        ([("item", 100)], False, "SAVE20", 80.0 + 60),
        # Member gets half shipping
        ([("item", 200)], True, None, 200.0 + 30),
    ],
)
def test_cart_total(items, member, coupon, total_expected):
    c = cart.Cart()
    for name, price in items:
        c.add_item(name, price)
    if coupon is not None:
        total = c.total(member=member, coupon=coupon)
    else:
        total = c.total(member=member)
    assert round(total, 2) == round(total_expected, 2)

# Test Cart total errors
@pytest.mark.parametrize("coupon", ["INVALID", "SAVE101"])
def test_cart_total_invalid_coupon(coupon):
    c = cart.Cart()
    c.add_item("item", 10)
    with pytest.raises(ValueError):
        c.total(coupon=coupon)
