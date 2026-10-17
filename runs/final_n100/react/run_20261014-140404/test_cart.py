import cart
import pytest

# -----------------------------
# Helper functions and fixtures
# -----------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

# -----------------------------
# Tests for apply_discount
# -----------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0


def test_apply_discount_rounding():
    # ensure rounding to two decimals
    assert cart.apply_discount(99.999, 10) == 90.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 20)


def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# -----------------------------
# Tests for bulk_discount_percent
# -----------------------------

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(200) == 15


def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-10)

# -----------------------------
# Tests for parse_coupon
# -----------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save50") == 50
    assert cart.parse_coupon(" SAVE20 ") == 20


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")

# -----------------------------
# Tests for shipping_fee
# -----------------------------

def test_shipping_fee_standard():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60


def test_shipping_fee_free_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0


def test_shipping_fee_member_discount():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# -----------------------------
# Tests for Cart class
# -----------------------------

def test_cart_initial_state(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0


def test_add_and_remove_item(empty_cart):
    empty_cart.add_item("Apple", 1.00, quantity=3)
    assert empty_cart.items()["Apple"] == (1.00, 3)
    empty_cart.remove_item("Apple", quantity=2)
    assert empty_cart.items()["Apple"] == (1.00, 1)


def test_add_invalid_price(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("Banana", -5.0)


def test_subtotal_calculation(empty_cart):
    empty_cart.add_item("A", 2.00, quantity=3)  # 6
    empty_cart.add_item("B", 1.50, quantity=2)  # 3
    assert empty_cart.subtotal() == 9.0


def test_total_with_member_and_coupon(empty_cart):
    empty_cart.add_item("Item", 100.0)
    # subtotal 100 -> no free shipping, member half fee
    total = empty_cart.total(member=True, coupon="SAVE10")
    # compute expected: apply bulk discount? quantity 1 => 0%
    expected_subtotal = 100.0
    discount_amount = cart.apply_discount(expected_subtotal, 10)
    shipping = cart.shipping_fee(discount_amount, member=True)
    assert total == discount_amount + shipping


def test_total_without_coupon(empty_cart):
    empty_cart.add_item("Item", 200.0)
    # no coupon: subtotal 200 -> shipping fee 60 (not member)
    total = empty_cart.total()
    assert total == 200.0 + 60

# -----------------------------
# Additional edge case tests
# -----------------------------

def test_bulk_discount_in_total(empty_cart):
    # quantity exactly 10 triggers 5% discount in total calculation via bulk
    empty_cart.add_item("Bulk", 10.0, quantity=10)
    # subtotal = 100
    total_no_coupon = empty_cart.total()
    expected = cart.apply_discount(100.0, cart.bulk_discount_percent(10)) + cart.shipping_fee(cart.apply_discount(100.0, cart.bulk_discount_percent(10)))
    assert total_no_coupon == expected
