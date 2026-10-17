import cart
import pytest

# --- apply_discount ---

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_edge_cases():
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)

def test_apply_discount_invalid_percent():
    for pct in [-1, 101]:
        with pytest.raises(ValueError):
            cart.apply_discount(100, pct)

# --- bulk_discount_percent ---

def test_bulk_discount_below_threshold():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(5) == 0


def test_bulk_discount_small_and_medium_large():
    # quantity thresholds according to spec
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(15) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(75) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(120) == 15


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# --- parse_coupon ---

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SaVe50 ") == 50


def test_parse_coupon_invalid_format_or_value():
    for code in ["DISCOUNT", "SAVE", "SAVE0", "SAVENOTNUMBER", "SAVE51"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# --- shipping_fee ---

def test_shipping_fee_free_and_member():
    assert cart.shipping_fee(1000, member=True) == 0.0
    assert cart.shipping_fee(1500, member=False) == 0.0
    assert cart.shipping_fee(999.99, member=True) == 30.0
    assert cart.shipping_fee(200, member=False) == 60.0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# --- Cart class tests ---

def test_cart_initial_state_and_add_remove_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 5.0, quantity=2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 5.0, quantity=3)
    assert c.items() == {"apple": 5}
    with pytest.raises(ValueError):
        c.add_item("apple", 6.0)
    c.remove_item("apple", quantity=3)
    assert c.items() == {"apple": 2}
    c.remove_item("apple", quantity=5)
    assert c.items() == {}


def test_cart_subtotal_bulk_discount_and_rounding():
    c = cart.Cart()
    # 10 units of $10 each -> 100 total, 5% discount -> 95
    c.add_item("widget", 10.0, quantity=10)
    assert c.subtotal() == 95.0
    c.add_item("gadget", 20.0, quantity=50)   # line total 1000, 10% discount -> 900
    assert round(c.subtotal(), 2) == 995.0  # 95 + 900 = 995


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("thing", 200.0, quantity=5)
    # subtotal: no bulk discount -> 1000
    assert c.subtotal() == 1000.0
    # non-member shipping 60
    assert c.total(member=False) == 1060.0
    # member shipping half 30
    assert c.total(member=True) == 1030.0
    # coupon SAVE10 -> 10% off subtotal -> 900 + 60 = 960 (non-member)
    assert c.total(member=False, coupon="SAVE10") == 960.0
    with pytest.raises(ValueError):
        c.total(coupon="INVALIDCODE")


def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
