import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# --- Test apply_discount ---

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (30, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --- Test bulk_discount_percent ---

def test_bulk_discount_percent_values():
    assert bulk_discount_percent(99) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty", [0, -3, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(int(qty)) if isinstance(qty, int) else bulk_discount_percent(qty)

# --- Test parse_coupon ---

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25 ") == 25
    assert parse_coupon("   SaVe50  ") == 50

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "saver5", "SAVEXY"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- Test shipping_fee ---

def test_shipping_fee():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=False) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Test Cart class ---

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == []
    assert cart.subtotal() == 0
    assert cart.total() == 60   # 0 subtotal -> fee 60, no discount

    cart.add_item("apple", 100, quantity=2)
    assert cart.items() == [("apple", 100, 2)]
    assert cart.subtotal() == 200
    # no coupon, not member
    assert cart.total() == 260   # subtotal + shipping(60)

    cart.add_item("banana", 50, quantity=3)
    # subtotal = 200 + 150 = 350
    assert cart.subtotal() == 350
    assert cart.total() == 410

    # apply coupon of 10%
    assert cart.total(coupon="SAVE10") == pytest.approx(369.0, rel=1e-5)

    # member discount also applied
    assert cart.total(member=True) == pytest.approx(350 + 30, rel=1e-5)  # subtotal+shipping

    # removing items
    cart.remove_item("apple", quantity=1)
    assert cart.items() == [("apple", 100, 1), ("banana", 50, 3)]
    assert cart.subtotal() == 250

    # bulk discount for banana: 3 units <10 => no bulk
    assert cart.total(coupon="SAVE5") == pytest.approx(310.0, rel=1e-5)
