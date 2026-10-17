import pytest
import cart

# Helper for approx equality
from math import isclose

def approx(a,b): return isclose(round(a,2), round(b,2), abs_tol=1e-9)

# ---------- Spec-based tests ----------

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0

# Adding single item: subtotal equals unit_price*qty; total includes shipping
def test_single_item_no_discount():
    c = cart.Cart()
    c.add_item("Apple", 1.00, quantity=3)
    assert approx(c.subtotal(), 3.00)
    # Shipping fee for subtotal<1000 is 60
    assert cart.shipping_fee(3.00) == 60
    expected_total = 3.00 + 60
    assert approx(c.total(), expected_total)

# Bulk discount triggers at quantity>=10,20 etc.
def test_bulk_discount_application():
    c = cart.Cart()
    c.add_item("BulkItem", 10.0, quantity=12)  # bulk discount 5%
    expected_subtotal = 12*10 * (1-0.05)
    assert approx(c.subtotal(), round(expected_subtotal,2))
    expected_total = expected_subtotal + cart.shipping_fee(expected_subtotal)
    assert approx(c.total(), round(expected_total,2))

# Coupon parsing and application per spec

def test_coupon_parsing_and_application():
    for code in ["SAVE10", "save20", " SAVE30 "]:
        percent = cart.parse_coupon(code)
        assert 1 <= percent <= 50
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")

    c = cart.Cart()
    c.add_item("Book", 20.0, quantity=5)  # subtotal 100
    total_with_coupon = c.total(coupon="SAVE10")
    # 10% off: 90 + shipping 60 =150
    assert approx(total_with_coupon, 150.00)

# Shipping fee rules and member discount per spec

def test_shipping_fee_and_member_discount():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(200, member=True) == 30
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Add item validation: price>=0, qty positive int

def test_add_item_validation():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("NegPrice", -1.0, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("ZeroQty", 5.0, quantity=0)

# Adding same item must have same unit price

def test_add_same_item_price_mismatch():
    c = cart.Cart()
    c.add_item("Pen", 1.00, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("Pen", 1.50, quantity=1)

# Removing items behavior

def test_remove_items():
    c = cart.Cart()
    c.add_item("Notebook", 3.0, quantity=5)
    c.remove_item("Notebook", quantity=2)
    assert c.items()["Notebook"] == 3
    # Remove more than remaining: item removed
    c.remove_item("Notebook", quantity=5)
    assert "Notebook" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("Notebook")

# Items dict is a copy

def test_items_is_copy():
    c = cart.Cart()
    c.add_item("Sticker", 0.5, quantity=10)
    d = c.items()
    d["Sticker"] = 99
    assert c.items()["Sticker"] == 10

# Coupon limits: N must be 1-50 inclusive

def test_coupon_limits():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")

# Bulk discount percent error on non-integer qty

def test_bulk_discount_invalid_qty():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(10.5)

# Apply discount errors per spec

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# Total respects member and coupon combination

def test_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item("Item", 200.0, quantity=10)  # subtotal before bulk: 2000; bulk 5% ->1900
    total = c.total(member=True, coupon="SAVE20")
    # Apply coupon to amount after bulk discount: 1900*0.8=1520; shipping free (subtotal>=1000)
    assert approx(total, 1520.00)
