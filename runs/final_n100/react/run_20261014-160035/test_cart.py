import pytest
from cart import (
    Cart,
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
)

# ---------- helper cart with items ----------

def build_cart():
    c = Cart()
    # add a few items
    c.add_item("apple", unit_price=1.0, quantity=3)   # subtotal 3.00
    c.add_item("banana", unit_price=0.5, quantity=2)  # subtotal +1.00 => total 4.00
    return c

# ---------- tests for helper functions ----------

def test_apply_discount_valid_and_errors():
    assert apply_discount(200.0, 15) == 170.0
    with pytest.raises(ValueError):
        apply_discount(-10, 10)
    with pytest.raises(ValueError):
        apply_discount(50, -5)
    with pytest.raises(ValueError):
        apply_discount(50, 105)

# Bulk discount percent rules

def test_bulk_discount_percent_cases():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

# Coupon parsing

def test_parse_coupon_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon(" SAVE30 ") == 30
    with pytest.raises(ValueError):
        parse_coupon("BADCODE")
    with pytest.raises(ValueError):
        parse_coupon("SAVE51")

# Shipping fee rules

def test_shipping_fee_rules():
    # Non‑member always pays full fee unless free threshold met
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    # Member pays half of the fee, but still must be below free threshold
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1500, member=True) == 0
    with pytest.raises(ValueError):
        shipping_fee(-5)

# ---------- tests for Cart methods ----------

def test_cart_items_structure():
    c = build_cart()
    items = c.items()
    assert isinstance(items, dict)
    # each value is a tuple (unit_price, quantity)
    for name, data in items.items():
        unit, qty = data
        assert isinstance(unit, float) or isinstance(unit, int)
        assert isinstance(qty, int)


def test_cart_subtotal():
    c = build_cart()
    # 3*1 + 2*0.5 = 4.0
    assert pytest.approx(c.subtotal()) == 4.0

# Total without coupon or member – shipping applied after subtotal

def test_cart_total_no_coupon_no_member():
    c = build_cart()
    expected_subtotal = 4.0
    # subtotal < 1000, so fee 60
    expected_total = round(expected_subtotal + 60, 2)
    assert pytest.approx(c.total()) == expected_total

# Total with a coupon – shipping based on discounted subtotal

def test_cart_total_with_coupon():
    c = build_cart()
    # apply coupon 10% => 3.6; add shipping fee for 3.6 (<1000, member=False) -> 60
    expected_subtotal_after_coupon = round(4.0 * (1 - 0.10), 2)
    assert pytest.approx(c.total(coupon="SAVE10")) == round(expected_subtotal_after_coupon + 60, 2)

# Total with member – shipping fee half after discount

def test_cart_total_with_member_and_coupon():
    c = Cart()
    # add one high‑value item to trigger free shipping for non‑member but not for member if below threshold
    c.add_item("luxury", unit_price=1200, quantity=1)
    # subtotal 1200; coupon 20% -> 960; shipping fee: subtotal >=1000 so free (fee 0)
    expected_total = round(960 + 0, 2)
    assert pytest.approx(c.total(member=True, coupon="SAVE20")) == expected_total

# Adding and removing items updates the internal state correctly

def test_add_and_remove_items():
    c = Cart()
    c.add_item("pen", unit_price=1.0, quantity=3)
    assert c.items()["pen"] == (1.0, 3)
    c.remove_item("pen", quantity=1)
    assert c.items()["pen"] == (1.0, 2)
    c.remove_item("pen")  # default quantity=1
    assert c.items()["pen"] == (1.0, 1)
    c.remove_item("pen", quantity=5)  # removing more than present should raise KeyError
    with pytest.raises(KeyError):
        c.remove_item("pen")  # trying to remove non‑existent item

# Removing an unknown item raises KeyError immediately

def test_remove_nonexistent_raises():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("ghost")
