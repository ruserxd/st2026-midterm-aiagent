import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Tests for utility functions ----------

def test_apply_discount_valid_cases():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    # rounding check: e.g., 199 * 0.15 = 29.85 discount -> 169.15
    assert apply_discount(199, 15) == round(199 * (1 - 0.15), 2)

@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)


def test_bulk_discount_percent_cases():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)


def test_parse_coupon_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe50 ") == 50
    # boundary conditions
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

@pytest.mark.parametrize("code", ["", "SAV10", "SAVE51", "123", " SAVE0 ", "SAVE-5", "SAVEabc"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)


def test_shipping_fee_cases():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

    # member discount halves fee when subtotal < 1000
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(999.99, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

def test_cart_initial_state():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0.0


def test_add_item_basic():
    cart = Cart()
    cart.add_item("apple", unit_price=100, quantity=2)
    assert cart.items()["apple"] == (100, 2)
    assert cart.subtotal() == 200.0

    # adding more of same item increases quantity but keeps price
    cart.add_item("apple", unit_price=100, quantity=3)
    assert cart.items()["apple"] == (100, 5)
    assert cart.subtotal() == 500.0


def test_remove_item():
    cart = Cart()
    cart.add_item("banana", 50, 5)  # subtotal 250
    cart.remove_item("banana", quantity=2)
    assert cart.items()["banana"] == (50, 3)
    assert cart.subtotal() == 150.0

    # removing more than present should raise error
    with pytest.raises(ValueError):
        cart.remove_item("banana", quantity=4)

    # removing non-existent item should raise error
    with pytest.raises(KeyError):
        cart.remove_item("cherry")


def test_cart_total_member_and_coupon():
    cart = Cart()
    cart.add_item("item1", 200, 10)  # subtotal 2000
    # bulk discount: quantity=10 -> percent 5
    expected_subtotal_after_bulk = apply_discount(2000, 5)

    total_no_coupon_member_false = (
        expected_subtotal_after_bulk + shipping_fee(expected_subtotal_after_bulk, member=False)
    )
    assert cart.total(member=False) == round(total_no_coupon_member_false, 2)

    # with coupon SAVE20 (20% off subtotal before shipping)
    total_with_coupon = (
        apply_discount(2000, 5)  # bulk
        * (1 - 0.20)            # coupon
        + shipping_fee(apply_discount(2000, 5) * (1 - 0.20), member=False)
    )
    assert cart.total(member=False, coupon="SAVE20") == round(total_with_coupon, 2)

    # as a member, shipping is half
    total_member = (
        apply_discount(2000, 5) * (1 - 0.20) + shipping_fee(apply_discount(2000, 5) * (1 - 0.20), member=True)
    )
    assert cart.total(member=True, coupon="SAVE20") == round(total_member, 2)


def test_cart_total_edge_cases():
    cart = Cart()
    # empty cart: total should be shipping fee? specification unclear; assume subtotal 0 -> shipping 60
    assert cart.total() == 60.0

    # invalid coupon raises ValueError
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")
