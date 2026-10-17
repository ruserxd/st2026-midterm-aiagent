import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ----- Utility helpers -------------------------------------------------

def approx(value, rel=1e-12):
    return pytest.approx(value, rel=rel)

# ----- Test function apply_discount -----------------------------------

def test_apply_discount_basic():
    assert apply_discount(200.0, 15) == 170.0
    assert apply_discount(100.0, 0) == 100.0
    assert apply_discount(50.0, 100) == 0.0

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (5, -1), (5, 101), (5, 200)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ----- Test bulk_discount_percent -------------------------------------

def test_bulk_discount_ranges():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [-1, 0, 3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ----- Test parse_coupon ----------------------------------------------

def test_parse_coupon_valid():
    for code in ["SAVE10", "save20", "  SaVe50 ", "SAVE1"]:
        percent = parse_coupon(code.strip()) if ' ' not in code else parse_coupon(code)
        # Ensure case-insensitive
        assert isinstance(percent, int)
        assert 1 <= percent <= 50
    assert parse_coupon(" SAVE10 ") == 10

@pytest.mark.parametrize(
    "code",
    [
        "", 'SAVE0', 'SAVE51', 'SAVEXX', 'SAVE-10', '123', 'SAVe',
        '   ', 'saVe99', 'save50x'
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ----- Test shipping_fee -----------------------------------------------

def test_shipping_fee():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(2000) == 0
    # member discount
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ----- Test Cart ----------------------------------------------------------

@pytest.fixture
def empty_cart():
    return Cart()


def test_add_and_items(empty_cart):
    cart = empty_cart
    cart.add_item("apple", 1.5, 2)
    cart.add_item("banana", 0.75, 3)
    assert cart.items() == {"apple": 2, "banana": 3}
    # Adding existing item increases quantity only if price matches
    cart.add_item("apple", 1.5, 1)
    assert cart.items()["apple"] == 3
    with pytest.raises(ValueError):
        cart.add_item("apple", 2.0, 1)  # price mismatch

@pytest.mark.parametrize(
    "name,price,quantity",
    [
        ("orange", -1, 1),
        ("pear", 1.0, 0),
        ("grape", 1.2, -3),
        ("peach", 0.5, "two")
    ],
)
def test_add_item_invalid(name, price, quantity):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item(name, price, quantity)


def test_remove_item(empty_cart):
    cart = empty_cart
    cart.add_item("carrot", 0.5, 4)
    cart.remove_item("carrot", 2)
    assert cart.items()["carrot"] == 2
    cart.remove_item("carrot", 2)  # should remove entirely
    assert "carrot" not in cart.items()
    with pytest.raises(KeyError):
        cart.remove_item("carrot", 1)

def test_subtotal_and_bulk_discount(empty_cart):
    cart = empty_cart
    cart.add_item("widget", 10.0, 9)   # no bulk discount
    assert cart.subtotal() == approx(90.0)
    cart.add_item("widget", 10.0, 1)   # total qty=10 -> 5% discount
    expected = 10.0 * 10 * 0.95
    assert cart.subtotal() == approx(expected)


def test_total_with_coupon_and_shipping(empty_cart):
    cart = empty_cart
    cart.add_item("itemA", 100.0, 1)  # subtotal 100
    # No coupon, non-member: shipping 60 -> total 160
    assert cart.total() == approx(160.0)
    # With valid coupon 10%
    assert cart.total(coupon="SAVE10") == approx(144.0)  # 90 + 60
    # Member discounts shipping to 30
    assert cart.total(member=True, coupon="SAVE20") == approx(108.0)


def test_total_empty_cart(empty_cart):
    cart = empty_cart
    assert cart.total() == 0

# ----- Run all tests ---------------------------------------------------
if __name__ == "__main__":
    pytest.main(["-q", __file__])
