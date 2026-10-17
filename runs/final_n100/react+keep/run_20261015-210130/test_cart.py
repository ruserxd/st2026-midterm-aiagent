import pytest
import cart
from decimal import Decimal, ROUND_HALF_UP

def round2(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

# Subtotal tests
@pytest.mark.parametrize(
    "items,expected",
    [
        ([], 0),
        ([{"name": "A", "unit_price": 10.0, "quantity": 1}], 10.0),
        ([{"name": "B", "unit_price": 5.0, "quantity": 12}], round2(5.0*12*(1-0.05))),
        ([{"name": "C", "unit_price": 3.0, "quantity": 55}], round2(3.0*55*(1-0.10))),
        ([{"name": "D", "unit_price": 20.0, "quantity": 120}], round2(20.0*120*(1-0.15))),
    ],
)
def test_subtotal(items, expected):
    c = cart.Cart()
    for i in items:
        c.add_item(i["name"], i["unit_price"], i["quantity"])
    assert round2(c.subtotal()) == expected

# Shipping fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Total tests with coupon and shipping
@pytest.mark.parametrize(
    "items,coupon,member,expected",
    [
        ([], None, False, 0),
        ([{"name": "E", "unit_price": 20.0, "quantity": 1}], None, False,
         round2(20.0 + 60)),
        ([{"name": "F", "unit_price": 100.0, "quantity": 1}], "SAVE10",
         False, round2((100 - cart.parse_coupon("SAVE10")) + 60)),
        ([{"name": "G", "unit_price": 200.0, "quantity": 1}], None,
         True, round2(200 + 30)),
    ],
)
def test_total(items,coupon,member,expected):
    c = cart.Cart()
    for i in items:
        c.add_item(i["name"], i["unit_price"], i["quantity"])
    assert round2(c.total(member=member, coupon=coupon)) == expected

# Invalid coupon raises ValueError

def test_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# bulk_discount_percent validation
@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_negative(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)
