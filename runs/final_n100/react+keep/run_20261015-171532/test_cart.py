import re
import pytest
import cart

# ---------- Utility function tests ----------

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),            # example from spec
    (100, 0, 100.0),             # no discount
    (50, 100, 0.0),              # full discount
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price,percent", [(-10, 20), (100, -5), (100, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Bulk discount tests
@pytest.mark.parametrize("quantity,expected", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Coupon parsing tests
VALID_CODES = {
    "SAVE10": 10,
    "save20": 20,
    "   SaVe30   ": 30,
}
@pytest.mark.parametrize("code,expected", VALID_CODES.items())
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

INVALID_COUPONS = ["SAV10", "SAVE0", "SAVE51", "save-5", "" , "  "]
@pytest.mark.parametrize("code", INVALID_COUPONS)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50.5])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == []
    c.add_item("apple", 100, quantity=2)
    assert c.items() == [("apple", 100, 2)]
    # adding same item increases quantity
    c.add_item("APPLE", 100)
    # names are case-sensitive by spec? assume they are identical only if exact string
    assert c.items() == [("apple", 100, 2), ("APPLE", 100, 1)]


def test_cart_remove_and_subtotal():
    c = cart.Cart()
    c.add_item("banana", 50, quantity=3)
    c.remove_item("banana", quantity=1)
    assert c.items() == [("banana", 50, 2)]
    assert c.subtotal() == 100
    # removing more than present should raise ValueError
    with pytest.raises(ValueError):
        c.remove_item("banana", quantity=5)


def test_cart_total_without_coupon_and_member():
    c = cart.Cart()
    c.add_item("milk", 200, quantity=2)   # subtotal 400
    assert c.total(member=False) == pytest.approx(460)  # 400 + shipping 60
    assert c.total(member=True) == pytest.approx(430)   # 400 + shipping 30


def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("bread", 150, quantity=4)
    subtotal = 600
    coupon_percent = cart.parse_coupon("SAVE10")
    discounted_subtotal = cart.apply_discount(subtotal, coupon_percent)
    # shipping after discount? assume based on original subtotal for simplicity
    expected_total_no_member = discounted_subtotal + 60
    assert c.total(coupon="SAVE10", member=False) == pytest.approx(expected_total_no_member)
    expected_total_member = discounted_subtotal + 30
    assert c.total(coupon="SAVE10", member=True) == pytest.approx(expected_total_member)

# Ensure invalid coupon raises ValueError in total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("chocolate", 100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
