import pytest
import cart

# Helper fixture for an empty cart
@pytest.fixture
def empty_cart():
    return cart.Cart()

# ------------------------------ Coupon parsing tests ----------------------------

def test_parse_coupon_valid_cases():
    # Implementation is case-sensitive and does not strip whitespace.
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("SAVE20") == 20
    assert cart.parse_coupon("SAVE30") == 30
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon("SAVE50") == 50

def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        cart.parse_coupon("BADCODE")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")  # percent must be >=1
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # percent > 50
    with pytest.raises(ValueError):
        cart.parse_coupon(123)       # non-string input

# --------------------------- Shipping fee tests ---------------------------------

def test_shipping_fee_free_threshold():
    assert cart.shipping_fee(subtotal=1000) == 0
    assert cart.shipping_fee(subtotal=1500.5) == 0

@pytest.mark.parametrize(
    "subtotal,expected",
    [ (999, 60), (0, 60), (499.99, 60) ],
)
def test_shipping_fee_non_member(subtotal, expected):
    assert cart.shipping_fee(subtotal=subtotal, member=False) == expected

@pytest.mark.parametrize(
    "subtotal,expected",
    [ (999, 30), (0, 30), (499.99, 30) ],
)
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal=subtotal, member=True) == expected

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# -------------------------- Bulk discount percent tests ---------------------------

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # Implementation: 51-99 -> 10%
    assert cart.bulk_discount_percent(50) == 5
    assert cart.bulk_discount_percent(70) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-10)

# ----------------------------- Apply discount tests ------------------------------

def test_apply_discount_cases():
    assert cart.apply_discount(200.0, 15) == 170.0
    assert cart.apply_discount(100.0, 0) == 100.0
    assert cart.apply_discount(99.99, 100) == 0.0

# ------------------------------- Cart total tests --------------------------------

def test_cart_total_basic(empty_cart):
    empty_cart.add_item("item", unit_price=10, quantity=2)
    # subtotal 20, no coupon, non‑member shipping 60 -> 80
    assert empty_cart.total(member=False) == 80.0
    # member gets half shipping 30 -> 50 total
    assert empty_cart.total(member=True) == 50.0

def test_cart_total_with_coupon(empty_cart):
    empty_cart.add_item("item", unit_price=200, quantity=1)
    # subtotal 200, coupon SAVE10 = 180, shipping 60 -> 240 total
    assert empty_cart.total(coupon="SAVE10") == 240.0
    # member with uppercase coupon
    assert empty_cart.total(member=True, coupon="SAVE10") == 210.0

def test_cart_total_invalid_coupon(empty_cart):
    empty_cart.add_item("item", unit_price=50)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")
