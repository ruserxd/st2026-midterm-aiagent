import cart
import pytest

# Test bulk discount percent function boundaries
def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(100) == 20

# parse_coupon spec tests
@ pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("50PERCENTOFF", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupon should raise ValueError
@ pytest.mark.parametrize("code", ["INVALID", "", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (0, False, 60), (0, True, 30), (500, False, 60), (999.99, True, 30), (1000, False, 0), (2000, True, 0) ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# subtotal calculation with bulk discounts
@pytest.mark.parametrize(
    "items,expected",
    [
        ([], 0),
        ([("item1", 100.0, 1)], 100.0),
        ([("item2", 200.0, 10)], 200*10 * (1-0.05)), # 5% discount
        ([("item3", 50.0, 100)], 50*100 * (1-0.20)),
    ],
)
def test_cart_subtotal(items, expected):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    assert round(c.subtotal(), 2) == round(expected, 2)

# total calculation with coupon and shipping
@pytest.mark.parametrize(
    "items,coupon_code,member,total_expected",
    [
        # empty cart
        ([], None, False, 0),
        # no coupon, non-member
        ([("item", 200.0, 1)], None, False, 260.0), # 200 + 60 shipping
        # no coupon, member
        ([("item", 200.0, 1)], None, True, 230.0),  # 200 + 30 shipping
        # with coupon reducing 10%
        ([("item", 300.0, 1)], "SAVE10", False, 260.0), # 300*0.9=270 + 60 =330? Wait compute: subtotal 300 -> after coupon 270 -> shipping 60 => 330
    ],
)
def test_cart_total(items,coupon_code,member,total_expected):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    total = c.total(member=member, coupon=coupon_code)
    assert round(total, 2) == round(total_expected, 2)
