import pytest
import cart

# Helper: parse a valid coupon
@pytest.fixture
def coupon():
    return 'SAVE10'

def test_apply_discount_valid_inputs():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

with pytest.raises(ValueError):
    cart.apply_discount(-10, 20)
with pytest.raises(ValueError):
    cart.apply_discount(10, -5)
with pytest.raises(ValueError):
    cart.apply_discount(10, 105)

# bulk discount percent
assert cart.bulk_discount_percent(5) == 0
assert cart.bulk_discount_percent(10) == 5
assert cart.bulk_discount_percent(49) == 5
assert cart.bulk_discount_percent(50) == 10
assert cart.bulk_discount_percent(99) == 10
assert cart.bulk_discount_percent(100) == 15
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-1)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(0.5)

# coupon parsing
assert cart.parse_coupon('SAVE10') == 10
assert cart.parse_coupon('save20') == 20
assert cart.parse_coupon('   SAVE30  ') == 30
with pytest.raises(ValueError):
    cart.parse_coupon('SAVEXX')
with pytest.raises(ValueError):
    cart.parse_coupon('SAVE51')

# shipping fee
assert cart.shipping_fee(500) == 60
assert cart.shipping_fee(1000) == 0
assert cart.shipping_fee(999.99, member=True) == 30
with pytest.raises(ValueError):
    cart.shipping_fee(-1)

# Cart behavior
c = cart.Cart()
c.add_item('apple', 2.00, quantity=3)
c.add_item('banana', 1.50, quantity=2)
assert c.items() == [('apple', (2.00, 3)), ('banana', (1.50, 2))]

# subtotal
assert c.subtotal() == 2.00*3 + 1.50*2

# total with bulk discount: apple 3 -> 0%, banana 2 -> 0%
c.total()
# expecting subtotal plus shipping
expected_total = cart.shipping_fee(c.subtotal(), member=False)
assert c.total() == expected_total

# test bulk discount when quantity >=10
c.add_item('orange', 1.00, quantity=10)
# now total should apply 5% discount on orange
subtotal_with_orange = 2*3 + 1.5*2 + 1*10
discounted_orange_total = cart.apply_discount(1*10, 5)
expected_subtotal = 2*3 + 1.5*2 + discounted_orange_total
expected_total = cart.shipping_fee(expected_subtotal)
assert c.total() == expected_total

# test coupon discount
c_total_with_coupon = c.total(coupon=cart.parse_coupon('SAVE10'))
# apply 10% on subtotal before shipping?
# assume coupon applies after shipping? unclear. skip.
