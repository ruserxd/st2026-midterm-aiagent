import pytest
import cart

# Helper for approximate equality due to rounding

def approx_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("SAVE20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupon: non-numeric suffix or out of range
@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "HELLO10", ""] )
def test_parse_coupon_invalid_non_numeric_or_range(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Cart.total tests ----------
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def sample_cart():
    c = cart.Cart()
    # item: unit price 12.34, quantity 3 - subtotal 37.02
    c.add_item("Widget", 12.34, 3)
    return c

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0.00

def test_total_without_coupon(sample_cart):
    subtotal = sample_cart.subtotal()
    assert approx_equal(subtotal, 37.02)
    total_no_coupon = sample_cart.total()
    # Total should be greater than subtotal due to shipping
    assert total_no_coupon > subtotal
    assert round(total_no_coupon, 2) == total_no_coupon

def test_total_with_valid_coupon(sample_cart):
    discounted = 37.02 * (1 - 0.10)
    expected_after_discount = round(discounted, 2)
    total_with_coupon = sample_cart.total(coupon="SAVE10")
    assert total_with_coupon > expected_after_discount
    assert round(total_with_coupon, 2) == total_with_coupon

def test_total_invalid_coupon(sample_cart):
    with pytest.raises(ValueError):
        sample_cart.total(coupon="SAVE100")

def test_member_shipping_behavior():
    c = cart.Cart()
    c.add_item("Item", 20, 1)
    total_non_member = c.total(member=False)
    total_member = c.total(member=True)
    # Member may have lower or equal shipping cost
    assert total_member <= total_non_member
