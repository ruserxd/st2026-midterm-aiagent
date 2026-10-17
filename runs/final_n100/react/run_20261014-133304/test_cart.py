import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_tiers():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    for code in ["SAVE10", "save10", " SAVE10 "]:
        assert parse_coupon(code) == 10
    assert parse_coupon("SaVe45") == 45

@pytest.mark.parametrize(
    "code",
    ["", "SAVE", "SAVE0", "SAVE51", "NOTC0UPON", "  SAVE-5 ", "SAVE10EXTRA"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_free_threshold():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.5) == 0

@pytest.mark.parametrize("subtotal", [999, 500])
def test_shipping_non_member(subtotal):
    assert shipping_fee(subtotal) == 60

@pytest.mark.parametrize("subtotal", [200, 700])
def test_shipping_member(subtotal):
    assert shipping_fee(subtotal, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart -------------------------------------------------------------

cart = Cart()

@pytest.fixture(autouse=True)
def reset_cart():
    cart.__init__()

def test_add_and_items():
    cart.add_item("apple", 100, quantity=3)
    cart.add_item("banana", 200)
    assert cart.items() == {
        "apple": (100, 3),
        "banana": (200, 1),
    }

def test_remove_item():
    cart.add_item("item", 50, quantity=5)
    cart.remove_item("item", quantity=2)
    assert cart.items()["item"] == (50, 3)
    with pytest.raises(ValueError):
        cart.remove_item("item", quantity=10)
    with pytest.raises(KeyError):
        cart.remove_item("doesnotexist")

def test_subtotal():
    cart.add_item("x", 100, quantity=2)
    cart.add_item("y", 300, quantity=1)
    assert cart.subtotal() == 500

# Helper to compute expected total with coupon and membership

def _expected_total(subtotal, member=False, coupon=None):
    fee = shipping_fee(subtotal, member=member)
    total = subtotal + fee
    if coupon:
        percent = parse_coupon(coupon)
        total = apply_discount(total, percent)
    return round(total, 2)

def test_total_with_coupon_and_member():
    cart.add_item("widget", 200, quantity=12)
    # bulk discount of 5% on this line
    subtotal = cart.subtotal() * 0.95
    total_expected = _expected_total(subtotal, member=True, coupon="SAVE10")
    assert cart.total(member=True, coupon="SAVE10") == total_expected

def test_total_basic():
    cart.add_item("gadget", 400)
    assert cart.subtotal() == 400
    assert cart.total() == 400

def test_total_bulk_discount_per_item():
    cart.add_item("item", 10, quantity=50)
    # subtotal = 500; bulk percent =10 - line total 450
    assert cart.total() == 450

def test_total_invalid_coupon():
    cart.add_item("item", 100)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")
