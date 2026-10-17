import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Utility fixtures ----------
@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def populated_cart(empty_cart):
    empty_cart.add_item("Apple", unit_price=100, quantity=5)
    empty_cart.add_item("Banana", unit_price=200, quantity=12)
    empty_cart.add_item("Cherry", unit_price=50, quantity=120)
    return empty_cart

# ---------- Tests for helper functions ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (1000, 0, 1000.0),
        (123.45, 50, 61.73),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize(
    "qty,expected",
    [(9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15)],
)
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

with pytest.raises(ValueError):
    bulk_discount_percent(0)
with pytest.raises(ValueError):
    bulk_discount_percent(-5)

# parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [("SAVE10", 10), ("save20", 20), (" SAVE30 ", 30)],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVEX", "SAVE51", "10SAVE", "", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (999.99, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    shipping_fee(-10, False)

# ---------- Tests for Cart class ----------

def test_cart_initially_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 0


def test_add_item_and_subtotal(populated_cart):
    cart = populated_cart
    expected_apple = apply_discount(100 * 5, bulk_discount_percent(5))
    expected_banana = apply_discount(200 * 12, bulk_discount_percent(12))
    expected_cherry = apply_discount(50 * 120, bulk_discount_percent(120))
    total_expected = round(expected_apple + expected_banana + expected_cherry, 2)
    assert cart.subtotal() == total_expected


def test_remove_item(populated_cart):
    cart = populated_cart
    cart.remove_item("Apple", quantity=3)
    expected_apple = apply_discount(100 * 2, bulk_discount_percent(2))
    banana_sub = apply_discount(200 * 12, bulk_discount_percent(12))
    cherry_sub = apply_discount(50 * 120, bulk_discount_percent(120))
    assert cart.subtotal() == round(expected_apple + banana_sub + cherry_sub, 2)
    cart.remove_item("Banana", quantity=12)
    assert "Banana" not in cart.items()

    with pytest.raises(KeyError):
        cart.remove_item("Nonexistent")

# Total calculation tests

def test_total_without_coupon(populated_cart):
    cart = populated_cart
    subtotal = cart.subtotal()
    shipping = shipping_fee(subtotal, member=False)
    expected = round(subtotal + shipping, 2)
    assert cart.total(member=False) == expected


def test_total_with_member(populated_cart):
    cart = populated_cart
    subtotal = cart.subtotal()
    shipping = shipping_fee(subtotal, member=True)
    expected = round(subtotal + shipping, 2)
    assert cart.total(member=True) == expected

# Coupon application tests
@pytest.mark.parametrize(
    "coupon_code",
    ["SAVE10", "save5", " SAVE20 "],
)
def test_total_with_coupon(populated_cart, coupon_code):
    cart = populated_cart
    subtotal = cart.subtotal()
    discounted_amount = apply_discount(subtotal, parse_coupon(coupon_code))
    expected_shipping = shipping_fee(discounted_amount, member=False)
    expected_total = round(discounted_amount + expected_shipping, 2)
    assert cart.total(coupon=coupon_code) == expected_total

# Test that an invalid coupon raises ValueError

def test_invalid_coupon(populated_cart):
    cart = populated_cart
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# ---------- Bug detection tests: compare implementation to spec ----------

# shipping based on subtotal AFTER discount vs BEFORE discount

def test_shipping_based_on_discounts():
    c = Cart()
    c.add_item("Item", unit_price=1100, quantity=1)
    coupon_code = "SAVE20"
    subtotal_before_coupon = c.subtotal()  # 1100
    discounted_amount = apply_discount(subtotal_before_coupon, parse_coupon(coupon_code))
    shipping_fee_after_discount = shipping_fee(discounted_amount, member=False)  # should be 60
    shipping_fee_impl = shipping_fee(subtotal_before_coupon, member=False)      # implementation uses original subtotal -> 0
    assert shipping_fee_after_discount != shipping_fee_impl
    expected_total_spec = round(discounted_amount + shipping_fee_after_discount, 2)
    assert c.total(coupon=coupon_code) == expected_total_spec

# Check that remove_item deletes when quantity reaches zero

def test_remove_item_removal_logic(populated_cart):
    cart = populated_cart
    cart.remove_item("Apple", quantity=5)
    assert "Apple" not in cart.items()
    with pytest.raises(KeyError):
        cart.remove_item("NonExistent")
