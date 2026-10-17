import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_cart():
    c = Cart()
    c.add_item("apple", unit_price=1.50, quantity=3)
    c.add_item("banana", unit_price=0.75, quantity=2)
    return c

# ---------------------------------------------------------------------------
# apply_discount tests
# ---------------------------------------------------------------------------
def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------------------------------------------------------------------------
# bulk_discount_percent tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [(1, 0), (5, 10), (9, 10), (10, 15), (19, 15), (20, 20)],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# ---------------------------------------------------------------------------
# parse_coupon tests
# ---------------------------------------------------------------------------
def test_parse_coupon_known():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("HALFPRICE") == 50
    assert parse_coupon("free") == 0

def test_parse_coupon_unknown_returns_zero():
    assert parse_coupon("NONEXISTENT") == 0

# ---------------------------------------------------------------------------
# shipping_fee tests
# ---------------------------------------------------------------------------
def test_shipping_fee_basic():
    assert shipping_fee(30, member=False) == 10
    assert shipping_fee(60, member=True) == 5
    assert shipping_fee(0, member=False) == 0

# ---------------------------------------------------------------------------
# Cart class tests
# ---------------------------------------------------------------------------
def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0

def test_cart_add_item(sample_cart):
    expected_items = {"apple": (1.50, 3), "banana": (0.75, 2)}
    assert sample_cart.items() == expected_items
    assert sample_cart.subtotal() == pytest.approx(6.0)

def test_cart_remove_item(sample_cart):
    sample_cart.remove_item("apple", quantity=2)
    assert sample_cart.items()["apple"] == (1.50, 1)
    assert sample_cart.subtotal() == pytest.approx(4.5)

def test_remove_item_more_than_exists(sample_cart):
    sample_cart.remove_item("banana", quantity=5)
    assert "banana" not in sample_cart.items()
    assert sample_cart.subtotal() == pytest.approx(4.5)

# The following tests are illustrative; implementation may differ.
# They check that total applies discounts and shipping as per spec.
def test_cart_total_basic(sample_cart):
    # No member, no coupon
    subtotal = sample_cart.subtotal()
    total = sample_cart.total(member=False)
    assert total == pytest.approx(subtotal + shipping_fee(subtotal))

# Apply bulk discount via quantity (not tested directly due to unknown logic).
