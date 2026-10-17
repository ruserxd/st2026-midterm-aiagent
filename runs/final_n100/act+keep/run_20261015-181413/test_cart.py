import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper data ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50.75, 20, 40.6),         # rounding test: 50.75 *0.8 = 40.6
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
valid_codes = {
    "SAVE10": 10,
    "save10": 10,
    " SAVE20 ": 20,
    "SaVe50": 50,
}

@pytest.mark.parametrize("code,expected", valid_codes.items())
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVE51", "discount10", "", "SAVEXY", 123]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),          # subtotal zero but non-member
        (999.99, False, 60),     # just below free threshold
        (1000, False, 0),        # exactly free threshold
        (1500, True, 30),        # member with free threshold not reached
        (1200, True, 0),         # member above threshold gets free shipping
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0

# Adding items and bulk discount effect

def test_cart_add_and_subtotal():
    cart = Cart()
    cart.add_item("apple", 1.00, quantity=10)   # triggers 5% discount -> 0.95 per unit
    assert cart.subtotal() == pytest.approx(9.5)
    cart.add_item("banana", 2.50, quantity=51)  # triggers 10% discount -> 2.25 per unit
    expected = 9.5 + (2.25 * 51)
    assert cart.subtotal() == pytest.approx(expected)

# Removing items

def test_cart_remove_item():
    cart = Cart()
    cart.add_item("orange", 3.00, quantity=4)
    cart.remove_item("orange", quantity=2)
    assert cart.items() == {"orange": 2}
    cart.remove_item("orange", quantity=2)  # should remove entirely
    assert cart.items() == {}
    with pytest.raises(KeyError):
        cart.remove_item("pear")

# add_item error when unit price mismatch

def test_cart_add_item_price_mismatch():
    cart = Cart()
    cart.add_item("mango", 5.00, quantity=1)
    with pytest.raises(ValueError):
        cart.add_item("mango", 6.00, quantity=2)

# total calculation: coupon + shipping

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("widget", 100.0, quantity=5)  # no bulk discount
    subtotal = 500.0
    # apply coupon SAVE10 -> 45%? wait percent 10 -> reduce 10%
    # after coupon: 450.0
    total_after_coupon = 450.0
    shipping = shipping_fee(total_after_coupon, member=False)  # subtotal<1000 so 60
    expected_total = round(total_after_coupon + shipping, 2)
    assert cart.total(coupon="SAVE10") == pytest.approx(expected_total)

# total with member and free shipping

def test_cart_total_member_free_shipping():
    cart = Cart()
    cart.add_item("expensive", 600.0, quantity=2)  # no bulk discount
    subtotal = 1200.0
    # no coupon
    shipping = shipping_fee(subtotal, member=True)
    assert shipping == 0
    expected_total = round(subtotal + shipping, 2)
    assert cart.total(member=True) == pytest.approx(expected_total)

# total on empty cart should be zero

def test_cart_total_empty():
    cart = Cart()
    assert cart.total() == 0
    assert cart.total(coupon="SAVE10") == 0

# invalid coupon raises ValueError in total

def test_cart_total_invalid_coupon():
    cart = Cart()
    cart.add_item("gadget", 50, quantity=1)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")
