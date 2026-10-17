import pytest
import cart

# Helper to build a cart from item specs

def build_cart(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [("SAVE10", 10), ("save5", 5), ("   SaVe25  ", 25)],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["", "SAVE0", "SAVE51", "INVALID", "SAVEx10"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- subtotal tests ----------
# Assuming bulk_discount_percent is 0 for qty<=5, else 10%
item_no_disc = ("A", 10.00, 3)   # no discount
item_bulk = ("B", 20.00, 6)      # 10% discount

def test_subtotal_single_no_discount():
    c = build_cart([item_no_disc])
    assert c.subtotal() == pytest.approx(30.00)

def test_subtotal_bulk_discount():
    c = build_cart([item_bulk])
    # 20*6=120 minus 10% =>108
    assert c.subtotal() == pytest.approx(108.00)

def test_subtotal_multiple_items():
    c = build_cart([item_no_disc, item_bulk])
    assert c.subtotal() == pytest.approx(138.00)

def test_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0.00

# ---------- total tests ----------
# Assume shipping_fee: 5% of subtotal (for member=False) if subtotal>0

def test_total_no_coupon():
    c = build_cart([item_no_disc])  # subtotal=30, shipping 1.5 =>31.5
    assert c.total() == pytest.approx(31.50)

def test_total_with_coupon():
    c = build_cart([item_no_disc])  # subtotal=30, coupon10% ->27, shipping 1.35 =>28.35
    assert c.total(coupon="SAVE10") == pytest.approx(28.35)

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.00

def test_total_invalid_coupon():
    c = build_cart([item_no_disc])
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
