import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- apply_discount tests -----

def test_apply_discount_basic():
    # Example from spec
    assert apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # Ensure rounding to two decimals
    assert apply_discount(99.99, 33) == round(99.99 * 0.67, 2)


def test_apply_discount_zero_percent():
    assert apply_discount(500, 0) == 500


def test_apply_discount_full_percent():
    assert apply_discount(1234.56, 100) == 0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ----- bulk_discount_percent tests -----

def test_bulk_discount_percent_none():
    assert bulk_discount_percent(5) == 0

def test_bulk_discount_percent_ten():
    assert bulk_discount_percent(10) == 5

def test_bulk_discount_percent_fifty():
    assert bulk_discount_percent(50) == 10

def test_bulk_discount_percent_hundred():
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ----- parse_coupon tests -----

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon(" SAVE5 ") == 5
    # Leading zeros allowed but must be within bounds
    assert parse_coupon("save05") == 5

@ pytest.mark.parametrize(
    "code",
    [
        "",            # empty string
        "SAV10",       # missing letter
        "SAVE0",       # below range
        "SAVE51",      # above range
        "SAVE-1",      # negative number
        "SAVEabc",     # non-digit
        "12345",       # wrong format
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- shipping_fee tests -----

def test_shipping_fee_free():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.50) == 0

def test_shipping_fee_non_member():
    assert shipping_fee(999) == 60
    assert shipping_fee(0) == 60

def test_shipping_fee_member_half():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Cart class tests -----

@pytest.fixture
def empty_cart():
    return Cart()


def test_cart_initially_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 60  # no items, member False => shipping fee 60


def test_add_item(empty_cart):
    empty_cart.add_item("apple", unit_price=2.5)
    assert empty_cart.items()["apple"] == (2.5, 1)
    assert empty_cart.subtotal() == 2.5


def test_add_multiple_quantities(empty_cart):
    empty_cart.add_item("banana", unit_price=1.0, quantity=3)
    assert empty_cart.items()["banana"] == (1.0, 3)
    assert empty_cart.subtotal() == 3.0


def test_remove_item_partial(empty_cart):
    empty_cart.add_item("orange", 4.0, quantity=5)
    empty_cart.remove_item("orange", quantity=2)
    assert empty_cart.items()["orange"] == (4.0, 3)
    assert empty_cart.subtotal() == 12.0


def test_remove_item_full(empty_cart):
    empty_cart.add_item("grape", 0.5, quantity=10)
    empty_cart.remove_item("grape")  # default quantity=1
    assert empty_cart.items()["grape"] == (0.5, 9)
    empty_cart.remove_item("grape", quantity=9)
    assert "grape" not in empty_cart.items()


def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")


def test_total_with_coupon_and_member(empty_cart):
    # 2 items, subtotal 1000 to trigger free shipping
    empty_cart.add_item("item1", 500)
    empty_cart.add_item("item2", 500)
    total = empty_cart.total(member=True, coupon="SAVE10")
    # subtotal 1000, shipping 0, bulk discount percent 5% for quantity=1 each
    # No bulk discounts apply. Coupon applies 10%
    expected_subtotal = 1000
    discounted = expected_subtotal * 0.90  # 10% off
    assert total == round(discounted, 2)


def test_total_without_coupon_member(empty_cart):
    empty_cart.add_item("single", 100)
    assert empty_cart.total(member=True) == 100 + 30  # shipping half for member


def test_total_bulk_discount_and_shipping():
    cart = Cart()
    cart.add_item("widget", unit_price=10, quantity=50)  # bulk discount 10%
    subtotal_before = 10 * 50
    discounted_subtotal = apply_discount(subtotal_before, bulk_discount_percent(50))
    assert cart.subtotal() == subtotal_before
    total = cart.total()
    # shipping fee 60 because subtotal <1000
    expected_total = round(discounted_subtotal + 60, 2)
    assert total == expected_total

# End of tests
