import pytest
import cart

# Helper to compare floats rounded to two decimals
from decimal import Decimal

def round2(x):
    return round(float(x), 2)

######################
# apply_discount tests
######################

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 10) == 90.0
    assert cart.apply_discount(50, 0) == 50.0

@ pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

###########################
# bulk_discount_percent tests
###########################

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.5)

##########################
# parse_coupon tests
##########################

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["", "INVALID", "SAVE0", "SAVE51", "SAVExx", "SAVET"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

##########################
# shipping_fee tests
##########################

def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

##########################
# Cart class tests
##########################

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # subtotal 0 + shipping fee 60, no discounts

# Adding items and totals

def test_add_and_total_non_member():
    c = cart.Cart()
    c.add_item("apple", 2.5, quantity=4)   # total 10
    assert c.items() == {"apple": 4}
    assert round2(c.subtotal()) == 10.0
    # subtotal <1000, member=False => shipping 60
    assert round2(c.total()) == 70.0

# Bulk discount applied by unit price

def test_bulk_discount_application():
    c = cart.Cart()
    # 12 units of same item should get 5% discount on that line
    c.add_item("banana", 1.0, quantity=12)
    assert round2(c.subtotal()) == 11.4   # 12 - 5%
    assert round2(c.total()) == 71.4

# Member discounts and coupon

def test_member_and_coupon():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=3)  # subtotal 600
    # member -> shipping fee half: 30
    # no bulk discount yet
    assert round2(c.total(member=True)) == 630.0
    # add coupon SAVE10 -> 10% off entire order before shipping
    c.add_item("gadget", 400, quantity=1)   # subtotal now 1000
    assert round2(c.subtotal()) == 1000.0
    # subtotal >=1000 => free shipping, coupon 10%
    assert round2(c.total(member=True, coupon="SAVE10")) == 900.0

# Remove items

def test_remove_items():
    c = cart.Cart()
    c.add_item("pen", 1.5, quantity=5)
    c.remove_item("pen", quantity=3)
    assert c.items() == {"pen": 2}
    c.remove_item("pen", quantity=2)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("pen")

# Adding item with different price raises ValueError

def test_add_same_item_different_price():
    c = cart.Cart()
    c.add_item("book", 10, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("book", 12, quantity=1)

# Invalid add parameters

def test_invalid_add_params():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("err", -5, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("err2", 5, quantity=0)
    with pytest.raises(ValueError):
        c.add_item("err3", 5, quantity=-2)
