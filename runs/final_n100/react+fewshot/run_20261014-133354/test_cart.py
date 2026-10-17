import pytest
import cart

# helper for rounding consistent with spec

def round2(x):
    return round(float(x), 2)

##############################
# Simple function tests
##############################

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-10, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount percent
@pytest.mark.parametrize("quantity,expected_percent", [
    (5, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected_percent):
    assert cart.bulk_discount_percent(quantity) == expected_percent

@pytest.mark.parametrize("quantity", [0, -3, 2.5, "ten"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
valid_codes = [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE5 ", 5),
]
@pytest.mark.parametrize("code,expected", valid_codes)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_coupons = ["", "SAVExx", "save0", "SAVE51", "1234", None]
@pytest.mark.parametrize("bad_code", invalid_coupons)
def test_parse_coupon_invalid(bad_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(bad_code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected_fee", [
    (1000, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member) == expected_fee

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

##############################
# Cart class tests
##############################

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, quantity=2)
    c.add_item("banana", 0.75)
    # adding same item increases quantity
    c.add_item("apple", 1.5, quantity=3)
    assert c.items() == {"apple":5, "banana":1}

    # remove some apples
    c.remove_item("apple", quantity=2)
    assert c.items()["apple"] == 3
    # removing all bananas removes key
    c.remove_item("banana")
    assert "banana" not in c.items()

    with pytest.raises(KeyError):
        c.remove_item("cherry")

    with pytest.raises(ValueError):
        c.add_item("pear", -1, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pear", 0.5, quantity=0)
    # price mismatch for existing item
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, quantity=1)

# subtotal calculations including bulk discount
def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 5 apples: no discount
    c.add_item("apple", 10.0, quantity=5)
    assert c.subtotal() == round2(50.0)  # 10*5
    # 10 bananas: 5% bulk discount
    c.add_item("banana", 4.0, quantity=10)
    banana_total = 40.0 * 0.95  # 5% off
    expected_sum = round2(50.0 + banana_total)
    assert round2(c.subtotal()) == expected_sum

# total with coupon and shipping
def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=3)  # 600 subtotal
    # apply coupon SAVE10 -> 10% off on 600 = 540
    total_after_discount = 540.0
    shipping = cart.shipping_fee(total_after_discount)
    expected_total = round2(total_after_discount + shipping)
    assert c.total(coupon="SAVE10") == expected_total
    # member gets half shipping; no coupon
    shipping_member = cart.shipping_fee(600, member=True)
    assert c.total(member=True) == round2(600 + shipping_member)

# total for empty cart is 0 (no shipping)
def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
