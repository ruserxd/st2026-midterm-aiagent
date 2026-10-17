import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 10) == 90.0
    # rounding behavior
    assert apply_discount(99.99, 5) == round(99.99 * 0.95, 2)

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -5)
    with pytest.raises(ValueValueError:=ValueError):
        apply_discount(100, 105)

# ---------- bulk_discount_percent tests (spec) ----------

def test_bulk_discount_spec_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_spec_errors():
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        bulk_discount_percent(0.5)

# ---------- parse_coupon tests (spec) ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon(" SAVE30 ") == 30

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        parse_coupon("SAVEXX")
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        parse_coupon("  save10s  ")

# ---------- shipping_fee tests (spec) ----------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

def test_shipping_fee_member():
    assert shipping_fee(400, member=True) == 30
    assert shipping_fee(950, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart tests (spec) ----------

def test_cart_basic_operations_spec():
    cart = Cart()
    cart.add_item("apple", 1.0, quantity=3)
    cart.add_item("banana", 2.5)
    assert cart.items() == {"apple": (1.0, 3), "banana": (2.5, 1)}
    assert cart.subtotal() == 3*1.0 + 1*2.5
    cart.remove_item("apple", quantity=1)
    assert cart.items()["apple"] == (1.0, 2)
    cart.remove_item("banana")
    assert "banana" not in cart.items()

def test_cart_total_no_coupon_member_free_shipping():
    cart = Cart()
    cart.add_item("item", 1200)
    assert cart.total(member=True) == round(1200 + shipping_fee(1200, member=True), 2)
    assert cart.total() == 1200

def test_cart_total_with_coupon_and_shipping():
    cart = Cart()
    cart.add_item("item", 200)
    amount_after_discount = apply_discount(200, parse_coupon("SAVE10"))
    expected = round(amount_after_discount + shipping_fee(200), 2)
    assert cart.total(coupon="SAVE10") == expected

def test_cart_total_empty():
    cart = Cart()
    assert cart.total() == 0
    assert cart.total(member=True) == 0
