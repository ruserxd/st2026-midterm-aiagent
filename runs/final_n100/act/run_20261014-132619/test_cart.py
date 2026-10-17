import pytest
from cart import Cart, parse_coupon, bulk_discount_percent

# Helper to create cart items
def make_cart(items):
    return Cart([{'unit_price': p, 'quantity': q} for p, q in items])

# ---------- Test parse_coupon -------------------------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30
    # boundary values
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        parse_coupon("SAVE0")   # below min
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")  # above max
    with pytest.raises(ValueError):
        parse_coupon("INVALID")
    with pytest.raises(ValueError):
        parse_coupon(123)
    with pytest.raises(ValueError):
        parse_coupon("SAV10")   # missing 'E'

# ---------- Test bulk_discount_percent ----------------------------------------

def test_bulk_discount_boundary():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)

# ---------- Test Cart.subtotal -------------------------------------------------

def test_cart_subtotal_single_item_no_discount():
    cart = make_cart([(20.0, 3)])  # 60 total
    assert cart.subtotal() == 60.00

def test_cart_subtotal_bulk_discount():
    # 12 units -> 5% discount on this item only
    cart = make_cart([(10.0, 12)])  # 120 * .95 = 114
    assert cart.subtotal() == 114.00

def test_cart_subtotal_multiple_items_with_discounts():
    cart = make_cart([
        (5.0, 15),   # 75 -> 5% discount => 71.25
        (20.0, 60)   # 1200 -> 10% discount => 1080
    ])
    assert cart.subtotal() == round(71.25 + 1080, 2)

def test_cart_subtotal_empty():
    cart = Cart([])
    assert cart.subtotal() == 0.00

# ---------- Test Cart.total -----------------------------------------------------

def test_cart_total_no_coupon_and_no_shipping_for_zero():
    cart = Cart([])
    assert cart.total() == 0.00

def test_cart_total_with_coupon_and_shipping():
    # Subtotal: 100 (10 items of $10 each) -> no bulk discount
    cart = make_cart([(10, 10)])
    # Apply coupon SAVE20 => 80 after discount
    assert cart.total('SAVE20') == pytest.approx(80.0 + cart.shipping_fee(), rel=1e-9)

def test_cart_total_shipping_calculation():
    # Subtotal 200 -> no discount; shipping fee should be applied on 200
    cart = make_cart([(20, 10)])  # 200
    expected = round(200 + cart.shipping_fee(), 2)
    assert cart.total() == expected

# ---------- Test Cart.shipping_fee (implied in total) ---------------------------
# Since shipping_fee is used internally, we test indirectly via total.

# ---------- Test integration of invalid coupon raises ValueError -----------------

def test_cart_total_invalid_coupon():
    cart = make_cart([(5.0, 1)])
    with pytest.raises(ValueError):
        cart.total('BADCODE')

# ---------- Edge case: large quantity triggering highest discount -----------

def test_cart_subtotal_highest_discount():
    cart = make_cart([(2.0, 150)])  # 300 * .85 = 255
    assert cart.subtotal() == 255.00
