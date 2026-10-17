import pytest

import cart

# ---------- Helper fixtures ----------
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def populated_cart(empty_cart):
    """Cart with a few items for testing."""
    empty_cart.add_item("apple", 2.5, quantity=4)
    empty_cart.add_item("banana", 1.0, quantity=10)
    empty_cart.add_item("cherry", 3.0)           # default quantity = 1
    return empty_cart

# ---------- Tests for standalone functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.00
    assert cart.apply_discount(50, 0) == 50.00
    assert cart.apply_discount(100, 100) == 0.00

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

def test_apply_discount_invalid_percent():
    for percent in (-5, 105):
        with pytest.raises(ValueError):
            cart.apply_discount(50, percent)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_invalid_quantity():
    for quantity in (0, -1, 3.14):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(quantity)


def test_parse_coupon_valid_cases():
    cases = [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SaVe30   ", 30),
        ("SaVE50", 50),
    ]
    for code, percent in cases:
        assert cart.parse_coupon(code) == percent


def test_parse_coupon_invalid_cases():
    invalid_codes = [
        "SAV10",          # missing E
        "SAVE0",          # N < 1
        "SAVE51",         # N > 50
        "XYZ123",
        "",
        " SAVE10A ",
        123,
    ]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)


def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# ---------- Tests for Cart class ----------

def test_cart_initially_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 60.0          # subtotal 0, member False => shipping 60


def test_add_item_and_items(populated_cart):
    items = populated_cart.items()
    assert items == {"apple": 4, "banana": 10, "cherry": 1}
    # Adding an existing item with same price
    populated_cart.add_item("apple", 2.5, quantity=6)
    assert populated_cart.items()["apple"] == 10


def test_add_item_invalid(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", -1, quantity=3)   # negative price
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 2, quantity=-5)   # negative quantity
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 2, quantity="two")# non‑int quantity


def test_add_item_price_mismatch(populated_cart):
    # apple already in cart at price 2.5; try different price
    with pytest.raises(ValueError):
        populated_cart.add_item("apple", 3.0, quantity=1)


def test_remove_item_and_items(populated_cart):
    # remove 4 apples -> left with 0 => removed entirely
    populated_cart.remove_item("apple", quantity=4)
    assert "apple" not in populated_cart.items()

    # remove 5 bananas from 10 -> left 5
    populated_cart.remove_item("banana", quantity=5)
    assert populated_cart.items()["banana"] == 5

    # removing more than existing removes item completely
    populated_cart.remove_item("cherry", quantity=2)     # only 1 in cart
    assert "cherry" not in populated_cart.items()


def test_remove_nonexistent(populated_cart):
    with pytest.raises(KeyError):
        populated_cart.remove_item("durian", quantity=1)


def test_subtotal_calculation(populated_cart):
    # apple:4*2.5 = 10, banana:10*1=10, cherry:1*3=3 => subtotal 23
    assert populated_cart.subtotal() == pytest.approx(23.0, rel=1e-9)


def test_total_with_member_and_coupon(populated_cart):
    # base subtotal 23 -> shipping 60 (subtotal < 1000)
    # member discount: shipping half = 30
    total_no_coupon = populated_cart.total(member=True)
    assert total_no_coupon == pytest.approx(53.0, rel=1e-9)

    # apply coupon SAVE10 => 10% off subtotal
    total_with_coupon = populated_cart.total(member=True, coupon="SAVE10")
    discounted_subtotal = 23 * (1 - 0.10)   # 20.7
    expected_total = discounted_subtotal + 30   # shipping for member
    assert total_with_coupon == pytest.approx(expected_total, rel=1e-9)

    # coupon with invalid code should raise
    with pytest.raises(ValueError):
        populated_cart.total(coupon="BADCODE")
