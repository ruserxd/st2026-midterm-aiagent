import pytest
import cart

# Helper for rounding as per apply_discount

def rounded(value):
    return round(value, 2)

@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent boundaries
@pytest.mark.parametrize("quantity, expected", [
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

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon valid and invalid
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    " SAVE30 ": 30,
    "SaVe5": 5,
}
@pytest.mark.parametrize("code, expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVE51", "DISCOUNT10", "", "1234", "SA VE10"]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (500, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == cart.shipping_fee(0.0)

def test_cart_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    # after adding
    assert c.items() == {"apple": (1.5, 2)}
    assert c.subtotal() == 3.0
    # add same item with same price increases quantity
    c.add_item("apple", 1.5, 3)
    assert c.items()["apple"] == (1.5, 5)
    # adding new item
    c.add_item("banana", 0.75)
    assert c.items()["banana"] == (0.75, 1)
    # test invalid add: price mismatch
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)
    # test invalid unit_price
    with pytest.raises(ValueError):
        c.add_item("pear", -1.0, 1)
    # test invalid quantity
    with pytest.raises(ValueError):
        c.add_item("pear", 1.0, 0)

def test_cart_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 3)
    c.remove_item("apple", 2)
    assert c.items()["apple"] == (1.5, 1)
    # remove remaining
    c.remove_item("apple", 1)
    assert "apple" not in c.items()
    # removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("orange", 1)

# total calculation including shipping and coupon
def test_cart_total_with_coupon_and_membership():
    c = cart.Cart()
    c.add_item("widget", 20.0, 5)  # subtotal 100
    # no member, no coupon
    expected_subtotal = 100.0
    expected_shipping = cart.shipping_fee(expected_subtotal)
    assert c.total() == expected_subtotal + expected_shipping
    # with membership
    assert c.total(member=True) == expected_subtotal + cart.shipping_fee(expected_subtotal, True)
    # with coupon 'SAVE10' (10% off subtotal before shipping?)
    coupon_percent = cart.parse_coupon("SAVE10")
    discounted = rounded(expected_subtotal * (1 - coupon_percent / 100))
    expected_total = discounted + cart.shipping_fee(discounted)
    assert c.total(coupon="SAVE10") == expected_total

# Ensure total respects member flag even with coupon
